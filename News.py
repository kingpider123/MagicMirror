import requests
from bs4 import BeautifulSoup

def News():
    url = 'https://www.kmdn.gov.tw/1117/1271/1272/'
    r1 = requests.get(url)
    r1.status_code

    coverpage = r1.content

    soup1 = BeautifulSoup(coverpage, 'html.parser')
    data1= soup1.find_all('div',class_='card')[0]
    coverpage_news= data1.select('ul li')
    return coverpage_news