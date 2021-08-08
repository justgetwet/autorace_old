import unittest
import results

class ResultsTest(unittest.TestCase):

    tpl = ("20210517", "伊勢崎", 11)

    def setUp(self):
        self.results = results.Results()
        self.soup = self.results.request(*self.tpl)

    def test_srOneRace(self):
        sr = self.results.srOneRace(*self.tpl)
        print(sr)
        self.assertEqual(len(sr), 13)

    def test_scrapeOneMonth(self):
        pass

    def test_request(self):
        tables = self.soup.find_all("table")
        self.assertEqual(len(tables), 4)

    # def test_racetitle(self):
    #     title = self.results.raceTitle(self.soup)
    #     self.assertEqual(type(title), str)

    # def test_bet_quinella(self):
    #     tpl = self.results.betQorE(self.soup, "2連複")
    #     race_title, ticket, dividend, result, recovery, balance = tpl
    #     self.assertEqual(type(race_title), str)
    #     self.assertEqual(ticket, "2連複")
    #     self.assertEqual(type(dividend), str)
    #     self.assertEqual(type(result), str)
    #     self.assertEqual(type(balance), int)

    # def test_bet_exacta(self):
    #     tpl = self.results.betQorE(self.soup, "2連単")
    #     race_title, ticket, dividend, result, recovery, balance = tpl
    #     self.assertEqual(type(race_title), str)
    #     self.assertEqual(ticket, "2連単")
    #     self.assertEqual(type(dividend), str)
    #     self.assertEqual(type(result), str)
    #     self.assertEqual(type(balance), int)

    # def test_srBet(self):
    #     date, place, race = self.t
    #     sr = self.results.srBet(date, place, race, "2連単")
    #     print(sr)
    #     self.assertEqual(len(sr), 6)

    # def test_dfBetOneDay(self):
    #     df = self.results.dfBetOneDay("20210517", "伊勢崎", "2連複")
    #     print(df)
    #     sdf = self.results.dfSummary(df)
    #     print(sdf)
    #     self.assertEqual(len(df), 12)
    #     self.assertEqual(len(sdf), 4)

    # def test_Test(self):
    #     df = self.results.Test()
    #     self.assertEqual(len(df), 12)

if __name__ == '__main__':
    unittest.main()
