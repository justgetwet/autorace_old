# -*- coding: utf-8 -*-
import urllib.request
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import re
import json
import pathlib
from datetime import datetime
pd.options.display.precision = 2

class MyTools:

    def get_soup(self, url):

        try: 
            html = urllib.request.urlopen(url)
        except urllib.error.URLError as e:
            print("URLError", e.reason)
            html = "<html></html>"

        soup = BeautifulSoup(html, "lxml")

        return soup

    def get_dfs(self, soup):

        dfs = [pd.DataFrame()]
        if soup.find("table") == None:
            print("get_dfs: a table is not found.")
        else:
            dfs = pd.io.html.read_html(soup.prettify())

        return dfs
        
    def df2jsonf(self, p: str, df: pd.DataFrame) -> None:
        
        rows = len(df)
        j = df.to_json(force_ascii=False)
        with open(p, "w", encoding="utf-8") as f:
            f.write(j)
        print(f"saved {p}: {rows} rows")
        
    def jsonf2df(self, p: str) -> pd.DataFrame:
    
        df = pd.DataFrame()
        f = pathlib.Path(p)
        if f.is_file():
            df = pd.read_json(p)
        else:
            print(f"{p} is not here.")
        
        return df
        
    def lst2jsonf(self, p: str, lst: list) -> None:
    
        elements = len(lst)
        j = json.dumps(lst)
        with open(p, "w", encoding="utf-8") as f:
            f.write(j)
        print(f"saved {p}: {elements} elements")
        
    
    def jsonf2lst(self, p: str) -> list:

        lst = []
        f = pathlib.Path(p)
        if f.is_file():
            with open(p, "r", encoding="utf-8") as f:
                lst = json.load(f)
        else:
            print(f"{p} is not here.")
            
        return lst
    
        
    def is_num(self, str_num):
        try:
            float(str_num)
        except ValueError:
            return False
        else:
            return True

class RaceSite:

    url_oddspark = "https://www.oddspark.com/autorace"
    
    url_racelist = url_oddspark + "/RaceList.do?"
    url_odds = url_oddspark + "/Odds.do?"
    url_pred = url_oddspark + "/yosou"
    url_result = url_oddspark + "/RaceResult.do?"
    url_kaisai = url_oddspark + "/KaisaiRaceList.do"

    url_oneday = url_oddspark + "/OneDayRaceList.do?"

    url_search = "https://www.oddspark.com/autorace/SearchPlayerResult.do?playerNm="
    search_opt = "&toAge=&totalVic=&retirementDv=0"

    placeCd_d = {'川口': '02', '伊勢崎': '03', '浜松': '04', '飯塚': '05', '山陽': '06'}
    placeEn_d = {'川口': 'kawaguchi', '伊勢崎': 'isesaki', '浜松': 'hamamatsu',\
                    '飯塚': 'iiduka', '山陽': 'sanyo'}


class Race(MyTools, RaceSite):

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


    def kaisaiRaces(self):
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
        
        return races
            
    def kaisai(self):
        races = self.kaisaiRaces()
        for race in races:
            print(race)

    def today(self):
        races = self.kaisaiRaces()
        races_today = [race.split() for race in races if race[-1:] == "*"]
        s_races_today = sorted(races_today, key=lambda x: x[2])
        races = []
        for races_p in s_races_today:
            yymmdd, place = re.sub("\(|\)|\'", "", races_p[3]).split(",")
            url_p = "raceDy=" + yymmdd + "&placeCd=" + self.placeCd_d[place]
            url = self.url_oneday + url_p
            soup = self.get_soup(url)
            title_tags = soup.select("a[href^='/autorace/RaceList.do?raceDy=']")[1:]
            titles = [re.sub("\xa0", " ", tag.text) for tag in title_tags]
            start_time_tags =  soup.select("span.start-time")
            start_times = [re.sub("\xa0", " ", tag.text) for tag in start_time_tags] 
            races += [place + " " + title + " " + start_time for title, start_time in zip(titles, start_times)]

        return races
        

if __name__=='__main__':

    races = Race().today()
    print(races)