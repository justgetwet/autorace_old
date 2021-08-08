import unittest
import autorace

class OneRaceTest(unittest.TestCase):

    # 1.開催レースの

    def setUp(self):
        r = "20210517", "伊勢崎", 1
        self.race = autorace.OneRace(*r)
        self.rows = self.race.rows

    def tearDown(self):
        pass

    def test_soup(self):
        tables = self.race.soup.find_all("table")
        self.assertEqual(len(tables), 1)

    def test_raceTitle(self):
        title = self.race.raceTitle()
        print(title)
        self.assertEqual(type(title), str)

    def test_raceTable(self):
        df = self.race.raceTable()
        cols = len(df.columns)
        rows = len(df)
        self.assertEqual(cols, 16)
        self.assertEqual(rows, self.rows)

    def test_dspRaceTable(self):
        pass

    def test_reqPrediction(self):
        dic, txt = self.race.reqPrediction()
        print(txt)
        rows = len(dic)
        self.assertEqual(rows, self.rows)
        self.assertEqual(type(txt), str)

    def test_setPrecition(self):
        self.race.setPrediction()
        dic = self.race.pred_d
        rows = len(dic)
        txt = self.race.sohyo
        self.assertEqual(rows, self.rows)
        self.assertEqual(type(txt), str)

    def test_reqOdds(self):
        dic = self.race.reqOdds()
        rows = len(dic)
        self.assertEqual(rows, self.rows)

    def test_setOdds(self):
        self.race.setOdds()
        dic = self.race.odds_d
        rows = len(dic)
        self.assertEqual(rows, self.rows)

    def test_reqAiPrediction(self):
        dic = self.race.reqAiPrediction()
        rows = len(dic)
        self.assertEqual(rows, self.rows)

    def test_setAiPrediction(self):
        self.race.setAiPrediction()
        dic = self.race.ai_d
        rows = len(dic)
        self.assertEqual(rows, self.rows)

    def test_p5raceTable(self):
        df = self.race.p5raceTable()
        cols = len(df.columns)
        rows = len(df)
        self.assertEqual(cols, 22)
        self.assertEqual(rows, self.rows)

    def test_dspP5raceTable(self):
        pass

    def test_scatter(self):
        bars = self.race.scatter()
        # 20210517 伊勢崎 1 問題あり
        print(bars)
        self.assertEqual(type(bars), str)

    def test_reqResult(self):
        df1, df2 = self.race.reqResult()
        cols1 = len(df1.columns)
        cols2 = len(df2.columns)
        self.assertEqual(cols1, 4)
        self.assertEqual(cols2, 12)

    def test_depResult(self):
        pass

    def test__detail(self):
        pass

    def test__entry(self):
        pass

    def test_to_html(slef):
        pass

if __name__ == "__main__":
    unittest.main()
    # t = AutoRaceTest()
    # t.test_reqResult()