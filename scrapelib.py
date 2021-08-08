import urllib.request
import pandas as pd
from bs4 import BeautifulSoup

def get_soup(url):

    try: 
        html = urllib.request.urlopen(url)
    except urllib.error.URLError as e:
        print("URLError", e.reason)
        html = "<html></html>"

    soup = BeautifulSoup(html, "lxml")

    return soup


def get_df(soup):

	df = pd.DataFrame()
	if soup.find("table") == None:
		print("a table is not found.")
	else:
		df = pd.io.html.read_html(soup.prettify())

	return df

# if not df.empty:
#	...
def is_num(str_num):
    try:
        float(str_num)
    except ValueError:
        return False
    else:
        return True



if __name__=='__main__':

	oddspark = "https://www.oddspark.com/autorace"
	s = get_soup(oddspark)
	d = get_df(s)
	print(d)
