# -*- coding: utf-8 -*-
import urllib.request
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import re
import seaborn as sns
import pickle
from datetime import datetime
pd.options.display.precision = 2

class ScrapeOddsPark:

    url_oddspark = "https://www.oddspark.com/autorace"
    
    url_race = url_oddspark + "/RaceList.do?"
    url_odds = url_oddspark + "/Odds.do?"
    url_pred = url_oddspark + "/yosou"
    url_result = url_oddspark + "/RaceResult.do?"
    url_kaisai = url_oddspark + "/KaisaiRaceList.do"

    placeCd_d = {'川口': '02', '伊勢崎': '03', '浜松': '04', '飯塚': '05', '山陽': '06'}
    placeEn_d = {'川口': 'kawaguchi', '伊勢崎': 'isesaki', '浜松': 'hamamatsu',\
                    '飯塚': 'iiduka', '山陽': 'sanyo'}

    def get_soup(self, url):

        try: 
            html = urllib.request.urlopen(url)
        except urllib.error.URLError as e:
            print("URLError", e.reason)
            html = "<html></html>"

        soup = BeautifulSoup(html, "lxml")

        return soup

    def get_df(self, soup):

        df = pd.DataFrame()
        if soup.find("table") == None:
            print("a table is not found.")
        else:
            df = pd.io.html.read_html(soup.prettify())

        return df

    def is_num(self, str_num):
        try:
            float(str_num)
        except ValueError:
            return False
        else:
            return True

class OneRace(ScrapeOddsPark):
    
    def __init__(self, date: str, place: str, race_no: int):

        self.race_no = race_no
        self.race = f"raceDy={date}&placeCd={self.placeCd_d[place]}&raceNo={str(race_no)}"
        self.pred = f"/{self.placeEn_d[place]}/{date[:4]}/{date[4:]}.html"
        self.ai = f"/ai/OneDayRaceList.do?raceDy={date}&placeCd={self.placeCd_d[place]}&aiId=1"
        
        url = self.url_race + self.race
        self.soup = self.get_soup(url)
        
        self.rows = len(self.soup.find_all("td", class_="showElm racer"))
        self.odds_d = { n : ("") for n in range(1, self.rows + 1)}
        self.pred_d = { n : ("", "", "") for n in range(1, self.rows + 1)}
        self.ai_d = { n : ("", "", "") for n in range(1, self.rows + 1)}
        self.sohyo = ""

        racetitle = self.raceTitle()
        print(racetitle)

    def raceTitle(self):
        shubetsu = self.soup.find("title").text.split('｜')[0].strip('【レース別出走表】') # 種別
        race = self.soup.find("title").text.split('｜')[1] # 日程 場所 レース
        start_time = self.soup.find('li', class_="RCstm").text.split()[1] # 発走時刻
        title = shubetsu + ' ' + race + ' ' + start_time
        return title

    def raceTable(self):

        df = self.get_df(self.soup)[0]
        idx = []
        rows = []
        for n in range(1, len(df)+1):
            racer_org = df.values[n-1][:6]
            # print(racer_org)
            racer = [re.sub("  |\u3000", " ", r) for r in racer_org if type(r) == str]
            # print(racer)
            # -> ['城戸 徹 41歳/27期 V0/0回/V1 ヤブキ３７３/1', '飯 塚', 
            # -> '0m 3.89 0.073', 'B-43 (B-46) 53.433', '3.39 3.463 3.423']
            name = racer[0].split()[0] + " " + racer[0].split()[1]
            age = racer[0].split()[2]
            rank = racer[3].split()[0]
            point = str(round(float(racer[3].split()[2]), 2))
            handicap = racer[2].split()[0]
            machine = re.sub("/1", "", racer[0].split()[4])
            belong = racer[1].replace(" ", "")
            # print(name, age, rank, point, handicap, machine, belong)
            avgTrial = float(racer[4].split()[0])
            avgRun = round(float(racer[4].split()[1]), 2)
            trial = racer[2].split()[1]
            trialDev = racer[2].split()[2]
            race_time = 0.0
            if self.is_num(trial):
                race_time = float(trial) + float(trialDev)
            handicap_int = int(handicap.strip("m")) / 10
            handi_1c = 0
            if n == 0: 
                handi_1c = 0.01 # 最内コース補正
            pred_time = "-"
            if self.is_num(trial):
                pred_time = round(race_time + float(0.01 * handicap_int) + handi_1c , 2)
            if self.is_num(trial):
                trial = float(trial)
            # print(avgTrial, avgRun, trial, trialDev, pred_time)
            odds = self.odds_d[n]
            pred = self.pred_d[n]
            cols = ["no", "name", "age", "rank", "point", "hand", "machine", "belong", "平試走", "平競争",]
            cols += ["実試走", "予競争", "odds", "予", "st", "comment"]
            row = [str(n), name, age, rank, point, handicap, machine, belong, avgTrial, avgRun]
            row += [trial, pred_time, odds, *pred]
            idx.append(n)
            rows.append(row)

        return pd.DataFrame(rows, index=idx, columns=cols)
    
    def dspRaceTable(self):
        df = self.raceTable()
        cm = sns.light_palette("green", as_cmap=True)
        display(df.style.background_gradient(cmap=cm).hide_index())
        print(self.sohyo)
    
    def setPrediction(self):
        if not self.sohyo:
            self.pred_d, self.sohyo = self.reqPrediction()
    
    def reqPrediction(self):
        url = self.url_pred + self.pred
        soup = self.get_soup(url)
        lst = soup.find_all("p", class_="sohyo")
        sohyo = "総評:" + lst[self.race_no - 1].find("strong").text.strip("（総評）")
        df = self.get_df(soup)
        _df = df[self.race_no - 1].dropna(thresh=9)
        pred_df = _df.fillna("")
        dic = {}
        for e in pred_df.itertuples():
            dic[int(e.車番)] = (e.晴, e.スタート, e.コメント)
            
        return dic, sohyo
    
    def setOdds(self):
        self.odds_d = self.reqOdds()
    
    def reqOdds(self):
        opt = "&betType=1&viewType=0"
        url = self.url_odds + self.race + opt
        soup = self.get_soup(url)
        _df = self.get_df(soup)[0]
        df = _df.fillna("")
        dic = {}
        for e in df.itertuples():
            dic[e.車番] = str(e.単勝オッズ)
        return dic
    
    def setAiPrediction(self):
        self.ai_d = self.reqAiPrediction()
    
    def reqAiPrediction(self):
        url = self.url_pred + self.ai
        soup = self.get_soup(url)
        _df = self.get_df(soup)[self.race_no - 1]
        df = _df.fillna("")
        dic = {}
        for e in df.itertuples():
            dic[e._1] = (e._5, e._6, e._7)
        
        return dic
    
    def p5raceTable(self):
        df = self.get_df(self.soup)[0]
        data = []
        for n in range(len(df)):
            racer_org = df.values[n][:6]
            racer = [re.sub("  |\u3000", " ", r) for r in racer_org if type(r) == str]
            name = racer[0].split()[0] + " " + racer[0].split()[1]
            hand = racer[2].split()[0]
            rank = racer[3].split()[0] + " " + racer[3].split()[1]
            lst = [str(n+1), name, hand, rank]
            for m in range(5):
                record = re.sub("  |\xa0", " ", df.values[n][m+8])
                records = re.sub('ST|試', '', record).split()
                r_hand = records[3]
                r_order = records[4]
                r_time = float(records[5])
                lst.extend([r_hand, r_order, r_time])
            ai_tpl = self.ai_d[n+1]
            lst.extend([*ai_tpl])
            data.append(lst)

        cols = ["no", "name", "hnd", "rank"]
        cols +=["1h", "1o", "1t", "2h", "2o", "2t", "3h", "3o", "3t", "4h", "4o", "4t", "5h", "5o", "5t"]
        cols +=["堅実", "一発", "直前"]

        return pd.DataFrame(data, columns=cols)

    def dsp5raceTable(self):
        pd.set_option('display.max_columns', 22)
        df = self.p5raceTable()

        def highlight(df):
            styles = df.copy()
            styles.loc[:,:] = ''
            for i in range(len(df)):
                for j in range(len(df.columns)):
                    if df.iloc[i, j] == '1着':
                        styles.iloc[i, j] = 'background-color: red'
                    if df.iloc[i, j] == '2着':
                        styles.iloc[i, j] = 'background-color: orange'
            return styles

        cm = sns.light_palette("green", as_cmap=True)
        display(df.style.background_gradient(cmap=cm).apply(highlight, axis=None).hide_index())
        bars = self.scatter()
        print(bars)
    
    def scatter(self):

        class Color:
            RED       = '\033[31m'
            END       = '\033[0m'

        def rank(s):
            rk = ""
            if s[0] == "S": rk = s.split("-")[1]
            if s[0] == "A": rk = str(int(s.split("-")[1]) + 48)
            if s[0] == "B": rk = str(int(s.split("-")[1]) + 280)
            return rk

        df = self.get_df(self.soup)[0]
        lst = [int(rank(df.values[i][4].split()[0])) // 5 for i in range(len(df))]
        lst.sort()
        bars = "S-1 "
        for i in range(80):
            if i == lst[0]:
                if len(lst) > 1: lst.pop(0)
                bars = bars + Color.RED + "|" + Color.END
            else:
                bars = bars + "|"
        bars = bars + "B-109"

        return bars
    
    def reqResult(self):
        
        pay_df = pd.DataFrame()
        result_df = pd.DataFrame()
        
        url = self.url_result + self.race
        soup = self.get_soup(url)

        if soup.select("table"):
            df = self.get_df(soup)
            result_df = df[0]
            lend2 = len(df[2])
            lend3 = len(df[3])
            pay = pd.merge(df[2].loc[[0, ],:], df[2].loc[[lend2-2, lend2-1], :], how="outer")
            pay_df = pd.merge(pay, df[3].loc[[lend3-2, lend3-1], :], how="outer")
            pay_df.columns = ['', '入賞', '配当', '人気']

        return pay_df, result_df

    def dspResult(self):
        pd.options.display.precision = 2
        pay_df, result_df = self.reqResult()
        if pay_df.empty:
            print("stop run!")
            return
        display(pay_df.style.hide_index())
        display(result_df.style.hide_index())

   
    # def clip(self):
    #     df = pd.io.html.read_html(self.soup.prettify())[0]
    #     with open('racerCode_d.pickle', 'rb') as f:
    #         racerCode_d = pickle.load(f)
    #     color_d = {1: "white", 2: "black", 3: "red", 4: "blue",\
    #                 5: "yellow", 6: "green", 7: "orange", 8: "hotpink"}
    #     lst = []
    #     for n in range(1, len(df) + 1):
    #         racer_link, racer_image, pred_comment = self.entry(df, racerCode_d, n)
    #         lst.append("<span style='color: " + color_d[n] + "'>■</span>")
    #         lst.append(racer_link)
    #         lst.append("<table>")
    #         lst.append("  <td width='100'>" + racer_image + "</td>")
    #         lst.append("  <td>" + pred_comment + "</td>")
    #         lst.append("</table>")

    #     pd.DataFrame([lst]).to_clipboard(sep='\n', header=False, index=False)

    #     full_title = self.soup.find("title").text
    #     r = full_title.split()[2].split("｜")[0]
    #     title = re.sub("【レース別出走表】", "", full_title.split()[0]) + r
    #     print(f"{title}: cliped!")

    def _detail(self, df, n):
        s = df.iloc[n-1, 6]
        # print(s)
        q10f = float(re.sub("：|%", "", s.split()[3]))
        q90f = float(re.sub("：|%", "", s.split()[9]))
        if q10f == q90f:
            arw = "➡️"
        elif q10f > q90f:
            arw = "⤴️"
        else:
            arw = "⤵️"
        k10 = re.sub("着順：", "", s.split()[0])
        k90 = re.sub("着順：", "", s.split()[6])
        q10 = "q:" + s.split()[3].strip("：")
        q90 = "q:" + s.split()[9].strip("：")
        st10 = "10st:" + s.split()[1]
        st90 = "90st:" + s.split()[7]
        res = " " + arw + " " + st10 + " " + q10 + " " + k10 + " / " + st90 + " " + q90 + " " + k90
        return res

    def _entry(self, df, racerCode_d, n):

        s = re.sub("\u3000", " ", df.iloc[n-1, 1])
        name = s.split()[0] + s.split()[1]
        age = s.split()[2]
        handicap = df.iloc[n-1, 3].split()[0]
        rank = df.iloc[n-1, 4].split()[0]
        detail = self._detail(df, n)
        racer = str(n) + " " + name + " " + rank + " " + handicap + " " + age
        img_name = rank + "_" + name
        img_file = img_name + ".jpg"

        url = "https://www.oddspark.com/autorace/PlayerDetail.do?playerCd="
        racer_url = url + racerCode_d[img_name]

        racer_link = "<a href='" + racer_url + "'>" + racer + "</a>"
        racer_link += "<span>" + detail + "</span>"
        racer_image = "<img src='./images/" + img_file + "' />"
        pred_comment = " " + self.pred_d[n][0] + " " + self.pred_d[n][2] + " st:" + self.pred_d[n][1]
        # print(pred_comment)
        return racer_link, racer_image, pred_comment
    
    def to_html(self):
        df = pd.io.html.read_html(self.soup.prettify())[0]
        with open('racerCode_d.pickle', 'rb') as f:
            racerCode_d = pickle.load(f)
        color_d = {1: "white", 2: "black", 3: "red", 4: "blue",\
                    5: "yellow", 6: "green", 7: "orange", 8: "hotpink"}
        tags = []
        for n in range(1, len(df) + 1):
            racer_link, racer_image, pred_comment = self._entry(df, racerCode_d, n)
            tags.append("<span style='color: " + color_d[n] + "'>■</span>")
            tags.append(racer_link)
            tags.append("<table>")
            tags.append("  <td width='100'>" + racer_image + "</td>")
            tags.append("  <td>" + pred_comment + "</td>")
            tags.append("</table>")

        html = ""
        for tag in tags:
            html += tag
        
        full_title = self.soup.find("title").text
        r = full_title.split()[2].split("｜")[0]
        title = re.sub("【レース別出走表】", "", full_title.split()[0]) + r
        print(title)

        return html

    def dspQuinella(self):
        pd.options.display.precision = 1
        def highlight(df):
            styles = df.copy()
            styles.loc[:] = ''
            for i in range(len(df)):
                if df.loc[i][0] == key:
                    styles.loc[i] = "background-color: orange"
            return styles

        opt = "&betType=6&viewType=0"
        url = self.url_odds + self.race + opt
        soup = self.get_soup(url)
        dfs = self.get_df(soup)
        # dfs = pd.io.html.read_html(soup.prettify())
        df = dfs[2]

        lst = []
        for n in range(len(df)):
            for m in range(len(df)-n):
                s = str(1+n) + "=" + str(m+2+n)
                l = [s, df.iloc[m, 1 + n*2]]
                lst.append(l)

        dic = dict(lst)        
        key = min(dic, key=dic.get)

        odds_df = pd.DataFrame(lst)

        odds_df.columns = ["車券", "配当"]
        cm = sns.light_palette("green", as_cmap=True)
        df_styles = odds_df.style.background_gradient(cmap=cm).apply(highlight, axis=None).hide_index()
        
        return df_styles


class Race(ScrapeOddsPark):

    def tuple_string_for_copy(self, s):
        # ("20210606", "飯塚") を作成
        tuple_string = ""
        if s[:2] == "20":
            kdate = s.split("(")[0]
            place = s.split()[1]
            date = datetime.strptime(kdate, "%Y年%m月%d日")
            sdate = str(date.year) + str(date.month).rjust(2, "0") + str(date.day).rjust(2, "0")
            tuple_string = "(" + "'" + sdate + "','" + place + "'" + ")"
        return tuple_string


    def today(self):
        soup = self.get_soup(self.url_kaisai)
        atags = soup.find("table").find_all("a")
        links = [a.get("href") for a in atags if a.get("href") != None]
        links.sort()
        pre_link = ""
        new_links = []
        for link in links:
            if pre_link != link:
                new_links.append(link)
            pre_link = link
        days = [link[9:] for link in new_links if link[10:16] == "OneDay"]
        races = []
        for day in days:
            
            url = self.url_oddspark + day
            soup = self.get_soup(url)
            # 年月日 + レース場
            kaisai_day = soup.find("title").text.split("｜")[0]
            # 1Rの発走時間
            time = "??:??"
            start_time = soup.find("span", class_="start-time")
            if start_time:
                time = soup.find("span", class_="start-time").text.replace("発走時間\xa0", "")
            # ("20210606", "飯塚")
            tps4cp = self.tuple_string_for_copy(kaisai_day)
            # 今日のraceに * 
            date_str = re.sub("=|&", " ", day).split()[1]
            date_str_now = datetime.now().strftime("%Y%m%d")
            mark = ""
            if date_str == date_str_now:
                mark = " *"

            kaisai = kaisai_day + " " + time + " " + tps4cp + mark
            races.append(kaisai)
        
        for race in races:
            print(race)


if __name__=='__main__':

    RaceHold().today()
    # pass
    # r = OneRace('20210613','浜松', 5)
    # df = r.raceTable()
    # print(df)
    # df1, df2 = r.reqResult()
    # print(df1.empty)
    # print(df2)
    # bars = race.scatter()
    # print(bars)
