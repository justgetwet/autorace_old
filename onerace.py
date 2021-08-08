# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import re
import json
import copy
import seaborn as sns
# from race import MyTools, RaceSite
from racers import Racers
# pd.set_option('display.max_columns', 22)

class OneRace(Racers):
    
    def __init__(self, date: str, place: str, race_no: int):

        self.json_path = "../../ruby/gosu/gosu_race/test_new.json"

        self.race_no = race_no
        self.p_race = f"raceDy={date}&placeCd={self.placeCd_d[place]}&raceNo={str(race_no)}"
        self.p_pred = f"/{self.placeEn_d[place]}/{date[:4]}/{date[4:]}.html"
        self.p_predai = f"/ai/OneDayRaceList.do?raceDy={date}&placeCd={self.placeCd_d[place]}&aiId=1"
        
        self.entry_soup = self.get_soup(self.url_racelist + self.p_race)
        self.result_soup = self.get_soup(self.url_result + self.p_race)
        
        self.pred_soup = ""
        self.predai_soup = ""
        self.row_size = len(self.entry_soup.find_all("td", class_="showElm racer"))
        self.odds_d = { n : ("") for n in range(1, self.row_size + 1)}
        self.pred_d = { n : ("", "", "") for n in range(1, self.row_size + 1)}
        self.predai_d = { n : ("", "", "") for n in range(1, self.row_size + 1)}
        self.sohyo = ""

        self.racetitle = self.raceTitle()
        print(self.racetitle)


    def raceTitle(self):
        # 一般戦 2021年6月25日(金) 伊勢崎 3R 15:21
        soup = self.entry_soup
        shubetsu, race = "OddsPark AutoRace", ""
        res = soup.find("title")
        if res and res.text != "オッズパークオートレース":
            shubetsu, race = res.text.split("｜")[:2] # race: 日程 場所 レース
            shubetsu = shubetsu.strip('【レース別出走表】') # 種別
        stm = soup.select_one(".RCstm")
        stm_txt = "spam ??:??" if not stm else stm.text
        start_time = stm_txt.split()[1] # 発走時刻
        dst = soup.select_one(".RCdst")
        dst_txt = "天候：?? 走路状況：?? spam" if not dst else dst.text
        weather, surface = dst_txt.split()[:2]
        surface = "(" + surface.strip("走路状況：") + ")"
        title = " ".join([shubetsu, race, start_time, weather, surface])
        return title
        
    def entry(self):
    
        df = self.get_dfs(self.entry_soup)[0]
        if df.empty: 
            return df
        sr_lst = []
        for n in range(len(df)):
            sr = self.sr_racer()
            racer_l = df.values[n][:7]
            racer = [re.sub("  |\u3000", " ", r) for r in racer_l if type(r) == str]
            # print(racer)
            # -> ['城戸 徹 41歳/27期 V0/0回/V1 ヤブキ３７３/1', '飯 塚', 
            # -> '0m 3.89 0.073', 'B-43 (B-46) 53.433', '3.39 3.463 3.423', '着順：0-0-0-7 0.16 ..']
            fstname, lstname, age, v, machine = racer[0].split()
            name = fstname + " " + lstname
            lg = racer[1].replace(" ", "")
            racer2s = racer[2].split()
            if "再" in racer2s: racer2s.remove("再") 
            handicap, tryLap, tryDev = racer2s # ハンデ、試走タイム、試走偏差
            rank, prvRank, point = racer[3].split() # ランク、(前ランク)、審査ポイント
            avgTry, avgLap, fstLap = racer[4].split() # 良10走lap
            # print(tryLap)
            last10, ast = racer[5].split()[:2] # 近10走着順、平均ST
            sr["no"] = str(n + 1)
            sr["name"] = name
            sr["age"] = re.sub("/", "-", age)
            sr["rank"] = rank
            sr["prank"] = prvRank
            sr["vc"] = re.sub("/", "-", v)
            sr["point"] = float(point)
            sr["last"] = last10.strip("着順：")
            sr['ast'] = ast
            sr["hand"] = handicap
            sr["machine"] = re.sub("/1", "", machine)
            sr["lg"] = lg
            if self.is_num(tryLap):
                sr["try"] = float(tryLap)
                sr["prd"] = float(tryLap) + float(tryDev)
            sr["avt"] = float(avgTry)
            sr["avg"] = float(avgLap)
            sr["fst"] = float(fstLap)
            sr.name = n
            sr_lst.append(sr)

        hands = [sr["hand"] for sr in sr_lst]
        avtLaps = [sr["avt"] for sr in sr_lst] 
        avgLaps = [sr["avg"] for sr in sr_lst]
        fstLaps = [sr["fst"] for sr in sr_lst]
        prdLaps = [sr["prd"] for sr in sr_lst]
        # avtDifs = self.calc_goalDifs(avtLaps, hands)
        avgDifs = self.calc_goalDifs(avgLaps, hands)
        fstDifs = self.calc_goalDifs(fstLaps, hands)
        prdDifs = self.calc_goalDifs(prdLaps, hands)
        for sr, avgDif, fstDif, prdDif in zip(sr_lst, avgDifs, fstDifs, prdDifs):
            # sr["atm"] = avtDif
            sr["avm"] = avgDif
            sr["fsm"] = fstDif
            sr["pdm"] = prdDif
        
        entry_df = pd.DataFrame(sr_lst)#.dropna(how="all", axis=1)
        
        return entry_df

    def dspEntry(self):
        df = self.entry().dropna(how="all", axis=1)
        cm = sns.light_palette("green", as_cmap=True)
        # print(self.racetitle)
        display(df.style.background_gradient(cmap=cm))


    def setOdds(self):
        self.odds_d = self.reqOdds()
    
    def reqOdds(self):
        opt = "&betType=1&viewType=0"
        url = self.url_odds + self.p_race + opt
        soup = self.get_soup(url)
        _df = self.get_dfs(soup)[0]
        odds_df = _df.fillna("")
        pred_df, sohyo = self.reqPrediction()
        df = pd.concat([odds_df, pred_df], axis=1)
        print(sohyo)
        display(df)
        # dic = {}
        # for e in df.itertuples():
        #     dic[e.車]
    def df_odds(self, dfs: list) -> pd.DataFrame:
        lst = []
        for df in dfs:
            for tri, odds in zip(df["車番"], df["オッズ"]):
                lst.append([re.sub("\xa0", "", tri), odds])
        s_lst = sorted(lst, key=lambda x: x[1])
        
        return pd.DataFrame(s_lst[:12])


    def dspOdds(self, fst_no: int, sec_no: int) -> pd.DataFrame:

        betType8 = "&viewType=0&betType=8" # trif
        betType9 = "&betType=9&viewType=1" # trio 人気順
        betType6 = "&betType=6&viewType=1" # quin 人気順
        fstNo = f"&bikeNo={fst_no}&jikuNo=1"
        secNo = f"&bikeNo={sec_no}&jikuNo=1"
        

        trif1_url = self.url_odds + self.p_race + betType8 + fstNo
        trif2_url = self.url_odds + self.p_race + betType8 + secNo
        trio_url = self.url_odds + self.p_race + betType9
        quin_url = self.url_odds + self.p_race + betType6
        trif1_soup = self.get_soup(trif1_url)
        trif2_soup = self.get_soup(trif2_url)
        trio_soup = self.get_soup(trio_url)
        quin_soup = self.get_soup(quin_url)
        trif1_dfs = self.get_dfs(trif1_soup)[2:]
        trif2_dfs = self.get_dfs(trif2_soup)[2:]
        trio_dfs = self.get_dfs(trio_soup)[2:4]
        quin_dfs = self.get_dfs(quin_soup)[2:4]
        trif1_df = self.df_odds(trif1_dfs)
        trif2_df = self.df_odds(trif2_dfs)
        trio_df = self.df_odds(trio_dfs)
        quin_df = self.df_odds(quin_dfs)

        df = pd.concat([trif1_df, trif2_df, trio_df, quin_df], axis=1)
        df.columns = ["trif1", "odds1", "trif2", "odds2", "trio", "odds3", "quin", "odds3"]
        display(df)

    def result(self):
    
        df = self.get_dfs(self.result_soup)[0]
        if df.empty: 
            return df
        s_df = df.sort_values('車')
        sr_odr, sr_fav = s_df["着"], s_df["人気"]
        odrs = [str(int(odr)) if self.is_num(odr) else odr for odr in sr_odr]
        favs = [str(int(fav)) if self.is_num(fav) else odr for fav in sr_fav]
        laps = list(s_df["競走タイム"])
        hands = list(s_df["ハンデ"])
        goalDiffs = self.calc_goalDifs(laps, hands)

        result_df = self.entry()
        for n in range(len(result_df)): 
            result_df.loc[n, "run"] = laps[n]
            result_df.loc[n, "rnm"] = goalDiffs[n]
            result_df.loc[n, "odr"] = odrs[n]
            result_df.loc[n, "fav"] = favs[n]
        
        return result_df
        
    def dspResult(self):
        df = self.result()
        cm = sns.light_palette("green", as_cmap=True)
        print(self.racetitle)
        display(df.style.background_gradient(cmap=cm).hide_index())

    def saveDf2json(self, df: pd.DataFrame):
        if df.empty:
            print("a dataframe is empty.")
            return
        j = df.to_json(force_ascii=False)
        dic = json.loads(j)
        title = self.racetitle
        dic["title"] = title
        j_with_title = json.dumps(dic, ensure_ascii=False)
        # p = "../../ruby/gosu/gosu_race/test_new.json"
        p = self.json_path
        with open(p, "w", encoding="utf-8") as f:
            f.write(j_with_title)
        print(f"saved dataframe: '{title}' to json")

    def savEntry(self):
        df = self.entry()
        self.saveDf2json(df)

    def savResult(self):
        df = self.result()
        self.saveDf2json(df)

    def reqPrediction(self):
        url = self.url_pred + self.p_pred
        soup = self.get_soup(url)
        lst = soup.find_all("p", class_="sohyo")
        sohyo = "総評:" + lst[self.race_no - 1].find("strong").text.strip("（総評）")
        dfs = self.get_dfs(soup)
        _df = dfs[self.race_no - 1].dropna(thresh=9)
        pred_df = _df.fillna("")
        lst = []
        for e in pred_df.itertuples():
            lst.append([e.晴, e.スタート, e.コメント])
            
        return pd.DataFrame(lst, columns=["晴", "ST", "Commnet"]), sohyo

    def srPayout(self):
        soup = self.result_soup
        dfs = self.get_dfs(soup)

        is_goal = dfs[1].iloc[0, 0] == "ゴール線通過"
        order_lst = list(dfs[0]["着"][:4])
        if type(order_lst[0]) == str:
            order_lst = [int(s) for s in order_lst if self.is_num(s)]
        is_order = order_lst == [1, 2, 3, 4]
        sr = pd.Series(0.0)
        if is_goal and is_order:
            race_title = soup.select_one("title").get_text().split("｜")[1]
            title = ["title", race_title]
            race_weather = soup.select_one("li.RCdst").get_text(strip=True).split()[0]
            race_weather = race_weather.strip("天候：")
            weather = ["wthr", race_weather]
            v1 = ["1st", dfs[0]["車"][0]]
            v2 = ["2nd", dfs[0]["車"][1]]
            v3 = ["3rd", dfs[0]["車"][2]]
            v4 = ["1stf", dfs[0]["人気"][0]]
            v5 = ["2ndf", dfs[0]["人気"][1]]
            v6 = ["3rdf", dfs[0]["人気"][2]]
            df2 = dfs[2].set_index(0)
            df3 = dfs[3].set_index(0)
            v7 = ["win", df2.at["単勝", 2]]
            v8 = ["quin", df2.at["2連複", 2]]
            v9 = ["exac", df2.at["2連単", 2]]
            v10 = ["trio", df3.at["3連複", 2]]
            v11 = ["trif", df3.at["3連単", 2]]
            values = [title, weather, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11]
            index, value = zip(*values)
            sr = pd.Series(value, index=index)

        return sr

    def dspPayout(self):
        sr = self.srPayout()
        print(sr)

    # def savPayout(self):
    #     sr = self.srPayout()
    #     j = sr.to_json(force_ascii=False)
    #     dic = json.loads(j)
    #     title =  dic["title"]
    #     p = "../../ruby/gosu/gosu_race/test_sr.json"
    #     with open(p, "w", encoding="utf-8") as f:
    #         f.write(j)
    #     print(f"saved payout: '{title}' to json")

    def bet(self, bets: list) -> None:
        sr = self.srPayout()
        winers =  [sr[odr] for odr in ["1st", "2nd", "3rd"]]
        title = sr['title']
        hits = [bet for bet in bets if bet in winers]
        
        pay = -3 * 1000
        
        if len(hits) > 1:
            pay_s = sr['quin']
            pay_i = int(re.sub("円|,", "", pay_s))
            pay = 3000 - pay_i * 10

        dic = {title: pay}
        print(dic)
    #     j = json.dumps(dic, ensure_ascii=False)
        p = "./mknk.json"
        
        new_d = {}
        try: # ファイルがなければ新規作成
            with open(p, mode='x') as f:
                json.dump(new_d, f)
                print(f"created: {p}")
        except FileExistsError:
            pass
        
        with open(p, "r", encoding="utf-8") as f:
            read_dic = json.load(f)

        read_dic.update(dic)

        read_j = json.dumps(read_dic, ensure_ascii=False)
        print(read_j)

        with open(p, "w", encoding="utf-8") as f:
            f.write(read_j)
            
        print(f"saved: '{title}' to json")

    def balance(self):
        p = "./mknk.json"
        with open(p, "r", encoding="utf-8") as f:
            read_dic = json.load(f)

        print(f"balance: {sum(read_dic.values())}")

if __name__=='__main__':

    race = OneRace('20210701','浜松', 3)
    print(race.racetitle)
    df = race.entry()
    print(df)
    # race.savResult()
    # print(df)
    
    # sr = race.srPayout()
    # print(sr)
    # race.bet([1, 2, 3])
    # race.balance()
    