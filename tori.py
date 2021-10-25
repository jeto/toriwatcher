from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
from datetime import datetime
import sched, time, requests

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
KEYWORD = os.getenv('KEYWORD')
URL = 'https://www.tori.fi/koko_suomi?q='+KEYWORD.replace(' ', '+')+'&st=s'
found = []
s = sched.scheduler(time.time, time.sleep)

def fetchTori(sc,init):
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find('div', class_='list_mode_thumb')
    try:
        elements = results.find_all('a', class_='item_row_flex')
        for element in elements:
            id = element['id']
            link = element['href']
            if id not in found:
                found.append(id)
                print(datetime.now().time(), "Found new listing", link)
                if not init:
                    postTelegram(link)
    except:
        print(datetime.now().time(), "No results")
    s.enter(300, 1, fetchTori, (sc,False,))

def postTelegram(message):
    url = 'https://api.telegram.org/bot'+TELEGRAM_TOKEN+'/sendMessage'
    payload = {'chat_id':CHAT_ID,'text':message}

    send = requests.post(url, data = payload)
    print(datetime.now().time(), send)

s.enter(1, 1, fetchTori, (s,True,))
s.run()
