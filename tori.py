from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
from datetime import datetime
import sched, time, requests, re

load_dotenv()

class item:
    def __init__(self, ID, price):
        self.ID = ID
        self.price = price

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
KEYWORD = os.getenv('KEYWORD')
URL = 'https://www.tori.fi/koko_suomi?q='+KEYWORD.replace(' ', '+')+'&st=s'
found = []
s = sched.scheduler(time.time, time.sleep)

found.append(item("item_89405600", 1400))

def fetchTori(sc,init):
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find('div', class_='list_mode_thumb')
    try:
        elements = results.find_all('a', class_='item_row_flex')
        if not elements:
            print(datetime.now().time(), "No results")
            return
        for element in elements:
            id = element['id']
            link = element['href']
            price = re.sub("[^0-9]", "", element.find('div', class_='desc_flex') \
                           .find('div', class_='ad-details-left') \
                           .find('div', class_='list-details-container') \
                           .find('p', class_='list_price').contents[0])
            if not any(x for x in found if x.ID == id):
                found.append(item(id, price))
                print(datetime.now().time(), "Found new listing", link)
                if not init:
                    postTelegram("Found new listing\n"+link)
            elif any(x for x in found if x.ID == id and x.price != price):
                for x in found:
                    if x.ID == id:
                        print(datetime.now().time(), "Price changed for item")
                        postTelegram("Price changed for item from "+str(x.price)+"€"+" to "+price+"€"+"\n"+link)
                        x.price = price
    except Exception as e:
        print(datetime.now().time(), "ERROR", e)
    s.enter(300, 1, fetchTori, (sc,False,))

def postTelegram(message):
    url = 'https://api.telegram.org/bot'+TELEGRAM_TOKEN+'/sendMessage'
    payload = {'chat_id':CHAT_ID,'text':message}

    send = requests.post(url, data = payload)
    print(datetime.now().time(), send)

s.enter(1, 1, fetchTori, (s,True,))
s.run()
