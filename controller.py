import requests
from dotenv import load_dotenv
import os
import docker
from datetime import datetime
from bottle import (
    run, post, response, request as bottle_request
)

load_dotenv()

class watcher:
    def __init__(self, index, keyword, chat_id, container):
        self.index = index
        self.keyword = keyword
        self.chat_id = chat_id
        self.container = container

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
watchers = []
update_id = 0

client = docker.from_env()

def gather_watchers():
    for index, container in enumerate(client.containers.list(), start=1):
        if container.attrs['Config']['Image'] == "tori":
            env = container.attrs['Config']['Env']
            keyword = [s for s in env if "KEYWORD" in s][0].split('=')[1]
            chat_id = [s for s in env if "CHAT_ID" in s][0].split('=')[1]
            watchers.append(watcher(index, keyword, int(chat_id), container.attrs['Id']))
gather_watchers()

def get_chat_id(data):
    chat_id = data['message']['chat']['id']
    return chat_id

def get_message(data):
    message = data['message']['text']
    return message

def get_update_id(data):
    update_id = data['update_id']
    return update_id

def post_telegram(chat_id, message):
    url = 'https://api.telegram.org/bot'+TELEGRAM_TOKEN+'/sendMessage'
    payload = {'chat_id':chat_id,'text':message}
    send = requests.post(url, data = payload)
    print(datetime.now().time(), send)

def get_watchers(chat_id):
    watcher_list = [w for w in watchers if w.chat_id == chat_id]
    return watcher_list

def create_watcher(keyword, chat_id):
    index = len(get_watchers(chat_id)) + 1
    container = client.containers.run('tori', \
            detach=True, \
            restart_policy={"Name":"on-failure","MaximumRetryCount":3}, \
            environment=["TELEGRAM_TOKEN="+TELEGRAM_TOKEN, \
                         "CHAT_ID="+str(chat_id), \
                         "KEYWORD="+keyword], \
            mem_limit="64m", \
            labels={"chat_id":str(chat_id),"keyword":keyword})
    watchers.append(watcher(index, keyword, chat_id, container.attrs['Id']))
    print("Watcher created for", keyword)

def delete_watcher(index, chat_id):
    try:
        watcher = [w for w in watchers if w.index == index and w.chat_id == chat_id][0]
        print(watcher.index, watcher.chat_id, watcher.container)
        container = client.containers.get(watcher.container)
        print(container)
        container.stop()
        watchers.remove(watcher)
        print("Removed watcher for", watcher.keyword)
        return True
    except IndexError:
        print("Couldn't find watcher with that id for that user")
        return False


@post('/')
def main():
    global update_id

    data = bottle_request.json
    if get_update_id(data) <= update_id:
        print("Old update, skipping")
        return
    update_id = get_update_id(data)
    print(data)
    message = get_message(data)
    chat_id = get_chat_id(data)
    if chat_id != ADMIN_ID:
        print("not admin")
        return
    if message.startswith("/add"):
        keyword = message[4:].strip()
        create_watcher(keyword, chat_id)
        post_telegram(chat_id, "Created watcher for " + keyword)
    if message.startswith("/delete"):
        index = int(message[7:].strip())
        if delete_watcher(index, chat_id):
            post_telegram(chat_id, "Deleted watcher " + str(index))
        else:
            post_telegram(chat_id, "Couldn't delete watcher")
    elif message == "/list":
        print("Printing toriwatchers")
        watcher_list = get_watchers(chat_id)
        if not watcher_list:
            post_telegram(chat_id, "You have no active watchers")
        else:
            reply = "You have following active watchers:\n"
            keywords = [str(w.index) + ". " + w.keyword for w in watcher_list]
            reply += "\n".join(keywords)
            post_telegram(chat_id, reply)

    return response

if __name__ == '__main__':
    run(host='localhost', port=3008, debug=True)

