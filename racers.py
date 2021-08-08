import numpy as np
import pandas as pd
import re
import json
from bs4 import BeautifulSoup
import seaborn as sns
import urllib.parse
import pathlib
from race import MyTools, RaceSite

class Racers(MyTools, RaceSite):

  names_path = "./racer_names.json"
  racers_path = "./racers.json"
  save_path = "../../ruby/gosu/gosu_race/test_new.json"
  # url_search = "https://www.oddspark.com/autorace/SearchPlayerResult.do?playerNm="
  # search_opt = "&toAge=&totalVic=&retirementDv=0"

  def sr_racer(self) -> pd.Series:

    name = "Racer Name"
    lst = ["no", "name", "age", "rank", "prank", "vc", "point", "last", "ast", "hand", "machine", "lg"]
    lst += ["try", "avt", "avg", "fst", "prd", "run", "avm", "fsm", "pdm", "rnm", "odr", "fav"]
    sr = pd.Series([np.nan] * len(lst), index=lst, name=name, dtype=object)

    return sr

  def soup_racer(self, name: str):
    # 
    utf_name = urllib.parse.quote(name)
    url_search = self.url_search + utf_name + self.search_opt 
    soup_s = self.get_soup(url_search)
    url_racer = soup_s.select_one("a[href^='/autorace/PlayerDetail.do?']").get("href").split("/")[2]
    url = self.url_oddspark + "/" + url_racer
    soup = self.get_soup(url)

    return soup

  def racer2sr(self, name: str) -> pd.Series:
    # 
    sr = self.sr_racer()
    soup = self.soup_racer(name)
    dfs = self.get_dfs(soup)
    
    name_s = soup.title.text
    name_l = re.sub("  |\u3000|（", " ", name_s).split()[:2]
    name = " ".join(name_l)    
    sr["name"] = name
    sr.name = name

    df1, df2, df5 = dfs[1].set_index(0), dfs[2].set_index(0), dfs[5].set_index(0)
    df4, df6 = dfs[4].set_index("種別"), dfs[6].set_index("種別")
    
    sr["age"] = df1.loc["年齢", 1] + "-" + df2.loc["期別", 1]
    sr["rank"] = df2.loc["現行ランク", 1]
    sr["prank"] = "(" + df2.loc["前期ランク", 1] + ")"
    year_v, youshutsu = df5.loc["通算V", 3].split("\xa0/\xa0")
    total_v = str(df5.loc["通算V", 1])
    sr["vc"] = "V" + year_v + "/" + youshutsu + "回/V" + total_v
    sr["point"] = df2.loc["審査ポイント", 1]
    fst = df4.loc["直近10走", "1着"]
    sec = df4.loc["直近10走", "2着"]
    trd = df4.loc["直近10走", "3着"]
    oth = df4.loc["直近10走", "着外"]
    sr["last"] = "-".join([str(fst), str(sec), str(trd), str(oth)])
    sr["lg"] = df2.loc["LG", 1]
    sr["avt"] = df6.loc["良10走", "平均試走T"]
    sr["avg"] = df6.loc["良10走", "平均競走T"]
    sr["fst"] = df6.loc["良10走", "最高競走T"]

    return sr
    
  def calc_goalDifs(self, laps: list, hands: list, mps=0.034) -> list:

    f_hands = [float(hand.strip("m")) for hand in hands]
    c1 = laps.pop(0)
    laps.insert(0, c1 + 0.01)
    goalTimes = [lap * (31.0 + f_hand/100) for lap, f_hand in zip(laps, f_hands)]
    goals = [gt for gt in goalTimes if gt != 0.0] # 失格など
    topTime = min(goals)
    goalDiffs = [(gt - topTime) / mps if gt != 0.0 else "-" for gt in goalTimes]

    return goalDiffs
    
  def picup_racers(self, ranks: list, hands: list, title: str) -> None:
  
    save_p = self.save_path
    racers_p = self.racers_path
    df = self.jsonf2df(racers_p)
    
    lst = [df[df["rank"] == rank].iloc[0, :] for rank in ranks]
    racers_df = pd.DataFrame(lst)
    
    avgLaps = [racers_df.loc[name, "avg"] for name in racers_df["name"]]
    fstLaps = [racers_df.loc[name, "fst"] for name in racers_df["name"]]
    avgDifs = self.calc_goalDifs(avgLaps, hands)
    fstDifs = self.calc_goalDifs(fstLaps, hands)

    for n, name in enumerate(racers_df["name"]):
        racers_df.loc[name, "no"] = str(n+1)
        racers_df.loc[name, "hand"] = hands[n]
        racers_df.loc[name, "avm"] = avgDifs[n]
        racers_df.loc[name, "fsm"] = fstDifs[n]

    racers_df.reset_index(drop=True, inplace=True)
    print(title)

    rdf = racers_df.dropna(how="all", axis=1)
    cm = sns.light_palette("green", as_cmap=True)
    display(rdf.style.background_gradient(cmap=cm))

    j = racers_df.to_json(force_ascii=False)
    j_dic = json.loads(j)
    j_dic["title"] = title
    j_with_title = json.dumps(j_dic, ensure_ascii=False)
    
    with open(save_p, "w", encoding="utf-8") as f:
        f.write(j_with_title)
    
    print(f"saved: {save_p} with title: {title}")


  def df_racers(self) -> pd.DataFrame:

    p = self.racers_path
    df = self.jsonf2df(p)

    return df.dropna(how="all", axis=1).sort_values('point', ascending=False)

    
  def create_racer_names_list(self):
    # ./images フォルダのjpgのファイル名から作成
    names_path = self.names_path # racer_names.json
    
    p_temp = list(pathlib.Path('./images').glob('*.jpg'))
    # -> WindowsPath('images/A-100_内山雄介.jpg')
    names = [str(p).split("_")[1].strip(".jpg") for p in p_temp]
    racer_j = json.dumps(names, ensure_ascii=False)
    with open(names_path, "w", encoding="utf-8") as f:
        f.write(racer_j)

  def create_racers_file(self) -> None:
    # 
    read_p = self.names_path # ./racer_names.json
    save_p = self.racers_path # ./racers.json
    
    names = self.jsonf2lst(read_p)
    # print(names[0])
    # lst = [r.racer2sr(name) for name in names]
    lst = []
    for name in names:
        sr = r.racer2sr(name)
        print(sr["rank"], sr.name)
        lst.append(sr)
        
    df = pd.DataFrame(lst)
    self.df2jsonf(save_p, df)

if __name__=='__main__':

  r = Racers()
  sr1 = r.racer2sr("東小野正道")
  sr2 = r.racer2sr("石貝武之")
  df = pd.DataFrame([sr1, sr2]).dropna(how="all", axis=1)
  print(df)
  # r.json_racers(df)
  # print(r.df_from_json())
