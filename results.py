import urllib.request
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import re
import seaborn as sns
import pickle
from datetime import datetime
import time
import random
import calendar

class ScrapeOddsPark:

    url_oddspark = "https://www.oddspark.com/autorace"
    
    url_race = url_oddspark + "/RaceList.do?"
    url_odds = url_oddspark + "/Odds.do?"
    url_pred = url_oddspark + "/yosou"
    url_result = url_oddspark + "/RaceResult.do?"

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
            
    def df2pickle(self, df: pd.DataFrame, file_name: str) -> None:
        
        with open(f"{file_name}.pickle", "wb") as f:
            pickle.dump(df, f)            
        print(f"a dataframe is saved to the {file_name}.pickle!")
        
            
    def pickle2df(self, file_name: str) -> pd.DataFrame:
    
        with open(f"{file_name}.pickle", "rb") as f:
            df = pickle.load(f)
        print(f"{file_name}.pickle is loaded.")
            
        return df

class Results(ScrapeOddsPark):

    def __init__(self):
        # self.url_oneday = self.url_oddspark + "/OneDayRaceRist.do?"
        pass

    def request(self, date: str, place: str, race: int):
        race = f"raceDy={date}&placeCd={self.placeCd_d[place]}&raceNo={str(race)}"
        url = self.url_result + race
        soup = self.get_soup(url)

        return soup

    def reqPrediction(self, date: str, place: str, race: int):
        slug = f"/{self.placeEn_d[place]}/{date[:4]}/{date[4:]}.html"
        url = self.url_pred + slug
        soup = self.get_soup(url)
        lst = soup.find_all("p", class_="sohyo")
        sohyo = "総評:" + lst[race - 1].find("strong").text.strip("（総評）")
        df = self.get_df(soup)
        _df = df[race - 1].dropna(thresh=9)
        pred_df = _df.fillna("")
        dic = {}
        dic[0] = ("", "", "", sohyo)
        # print(pred_df)
        for e in pred_df.itertuples():
            dic[int(e.車番)] = (e.晴, e.選手名, e.スタート, e.コメント)
            
        return dic

    def dspPrediction(self, dic: dict) -> pd.DataFrame:
        swp_d = {v[0]: (k, v[1], v[2], v[3]) for k, v in dic.items() if not v[0] == ""}
        # print(swp_d)
        print(dic[0][3])
        marks = ["◎", "○", "▲", "△", "×"]
        lst = [(mark, *swp_d[mark]) for mark in marks]
        cols = ["予", "車", "選手名", "ST", "コメント"]
        df = pd.DataFrame(lst)
        df.columns = cols

        return df

    def resultSoup(self, date: str, place: str, race: int):

        slug = f"raceDy={date}&placeCd={self.placeCd_d[place]}&raceNo={str(race)}"
        url = self.url_result + slug

        return self.get_soup(url)


    def OneRace2Sr(self, date: str, place: str, race: int)-> pd.Series:

        sr = pd.Series(dtype="object")
        slug = f"raceDy={date}&placeCd={self.placeCd_d[place]}&raceNo={str(race)}"
        url = self.url_result + slug
        soup = self.get_soup(url)
        df = self.get_df(soup)
        if not len(df):
            return sr
        is_goal = df[1].iloc[0, 0] == "ゴール線通過"
        is_order = list(df[0]["着"][:4]) == [1, 2, 3, 4]
        if is_goal and is_order:
            race_title = soup.select_one("title").get_text().split("｜")[1]
            race = ["race", race_title]
            race_weather = soup.select_one("li.RCdst").get_text(strip=True).split()[0]
            race_weather = race_weather.strip("天候：")
            weather = ["wthr", race_weather]
            v1 = ["fst", df[0]["車"][0]]
            v2 = ["sec", df[0]["車"][1]]
            v3 = ["thd", df[0]["車"][2]]
            df2 = df[2].set_index(0)
            v4 = ["win", df2.at["単勝", 2]]
            v5 = ["quin", df2.at["2連複", 2]]
            v6 = ["exac", df2.at["2連単", 2]]
            df3 = df[3].set_index(0)
            v7 = ["trio", df3.at["3連複", 2]]
            v8 = ["trif", df3.at["3連単", 2]]
            fav_d = { r.人気: r.車 for r in df[0].itertuples()}
            if type(list(fav_d.keys())[0]) == str:
                fav_d = {int(key): fav_d[key] for key in fav_d if key.isdecimal()}
            fav_l = [fav_d[i] if fav_d.get(i) else 0 for i in [1, 2, 3]]
            if 0 in fav_l:
                print(fav_d)
            v9 = ["fv1", fav_l[0]]
            v10 = ["fv2", fav_l[1]]
            v11 = ["fv3", fav_l[2]]
            values = [race, weather, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11]
            index, value = zip(*values)
            sr = pd.Series(value, index=index)

        return sr

    def scrapeOneMonth(self, year: int, month: int)-> None:
        days = calendar.monthrange(year, month)[1]
        lst = []
        for i in range(1, days + 1):
            for place in self.placeCd_d.keys():
                yyyymmdd = str(year) + str(str(month).rjust(2, "0")) + str(i).rjust(2, "0")
                url = self.url_result + f"raceDy={yyyymmdd}&placeCd={self.placeCd_d[place]}"
                soup = self.get_soup(url)
                title = soup.find("title").text
                # print(yyyymmdd, key, title)
                is_empty = title == "オッズパークオートレース"
                if not is_empty:
                    print(title)
                    for r in range(1, 13):
                        time.sleep(random.random())
                        sr = self.OneRace2Sr(yyyymmdd, place, r)
                        if not sr.empty:
                            lst.append(sr)
                            
        df = pd.DataFrame(lst)
        filename = "arResult_" + str(year) + str(month).rjust(2, "0")
        
        self.df2pickle(df, filename)

        return None


    def simula_favorite(self, df: pd.DataFrame, ticket: str) -> pd.DataFrame:
        
        result_df = pd.DataFrame()
        
        bet_d = {"単勝": 30, "2連複": 10, "2連単": 5, "3連複": 30, "3連単": 5}
        if not ticket in bet_d.keys():
            print("key error: keys are '単勝', '2連複', '2連単', '3連複', '3連単'")
            return result_df    
        lst = []
        for r in df.itertuples():
            
            judgement = False
            judge = "x"
            dividend = 0
            divide = ""
            drop_cols = []
            if ticket == "単勝":
                judgement = r.fst == r.fv1
                divide = r.win
                drop_cols = ["quin", "exac", "trio", "trif"]
            if ticket == "2連複":
                judgement = set([r.fst, r.sec]) <= set([r.fv1, r.fv2, r.fv3])
                divide = r.quin
                drop_cols = ["win", "exac", "trio", "trif"]
            if ticket == "2連単":
                judgement = set([r.fst, r.sec]) <= set([r.fv1, r.fv2, r.fv3])
                divide = r.exac
                drop_cols = ["win", "quin", "trio", "trif"]
            if ticket == "3連複":
                judgement = set([r.fst, r.sec, r.thd]) == set([r.fv1, r.fv2, r.fv3])
                divide = r.trio
                drop_cols = ["win", "quin", "exac", "trif"]
            if ticket == "3連単":
                judgement = set([r.fst, r.sec, r.thd]) == set([r.fv1, r.fv2, r.fv3])
                divide = r.trif
                drop_cols = ["win", "quin", "exac", "trio"]
                
            if judgement:
                judge = "o"
                dividend = int(re.sub(",|円", "", divide)) * bet_d[ticket]
                
            balance = dividend - 3000
            result = (r.race, judge, dividend, balance)
            index = ("race", "jdg", "divd", "blnc")
            sr = pd.Series(result, index=index)
            lst.append(sr)

        result_df = df.drop(drop_cols, axis=1).merge(pd.DataFrame(lst))
        
        return result_df

    def summary2Sr(self, df: pd.DataFrame) -> pd.Series:

        dic = {"win": "単勝", "quin": "2連複", "exac": "2連単", "trio": "3連複", "trif": "3連単"}
        ticket = dic[df.columns[5]]
        wins = [j for j in df["jdg"] if j == "o"]
        hit_rate = round(len(wins) / len(df), 2)
        recovery_rate = round(sum(df["divd"]) / (len(df) * 3000), 2)
        v1 = ["race", len(df)]
        v2 = ["ticket", ticket]
        v3 = ["Hit rate", hit_rate]
        v4 = ["Recovery", recovery_rate]
        v5 = ["Balance", sum(df["blnc"])]
        values = [v1, v2, v3, v4, v5]
        index, value = zip(*values)
        sr = pd.Series(value, index=index)
        
        return sr

    def arSummary(self, df: pd.DataFrame) -> pd.DataFrame:
        lst = []
        for ticket in ["単勝", "2連複", "2連単", "3連複", "3連単"]:
            r_df = self.simula_favorite(df, ticket)
            sr = self.summary2Sr(r_df)
            lst.append(sr)

        return pd.DataFrame(lst)

if __name__=='__main__':

    r = Results()
    
    # r.scrapeOneMonth(2021, 3)

    # r_df = r.pickle2df("arResult_202104")
    # df = r.arSummary(r_df)
    # print(df)
    dic = r.reqPrediction("20210526", "川口", 5)
    df = r.dspPrediction(dic)
    print(df)
    
