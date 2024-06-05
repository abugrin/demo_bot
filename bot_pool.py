import os

from time import sleep
from requests import post
from dotenv import load_dotenv

load_dotenv()
url = "https://botapi.messenger.yandex.net/bot/v1/messages/getUpdates"

headers = {
    "Authorization": f"OAuth {os.getenv('BOT_KEY')}",
    "ContentType": "application/json"
}


class Chat:
    def __init__(self, chat_type, chat_id='0', thread_id='0'):
        self.chat_id = chat_id
        self.chat_type = chat_type
        self.thread_id = thread_id


class From:
    def __init__(self, display_name, from_id, login, robot):
        self.display_name = display_name
        self.from_id = from_id
        self.login = login
        self.robot = robot


class Update:
    def __init__(self, chat: Chat, from_m: From, message_id, text, timestamp,
                 update_id, reply_to_message=None, callback_data=None):
        self.chat = chat
        self.from_m = from_m
        self.message_id = message_id
        self.text = text
        self.timestamp = timestamp
        self.update_id = update_id
        self.reply_to_message = reply_to_message
        self.callback_data = callback_data


def create_reply_update(reply_to_message):
    if 'id' in reply_to_message['chat']:
        chat_id = reply_to_message['chat']['id']
    else:
        chat_id = '0'

    chat = Chat(chat_id=chat_id, chat_type=reply_to_message['chat']['type'], thread_id='0')
    from_m = From(display_name=reply_to_message['from']['display_name'],
                  from_id=reply_to_message['from']['id'],
                  login=reply_to_message['from']['login'],
                  robot=reply_to_message['from']['robot'])

    return Update(chat=chat, from_m=from_m,
                  message_id=reply_to_message['message_id'],
                  text=reply_to_message['text'],
                  timestamp=reply_to_message['timestamp'],
                  update_id='0')


def create_update(update):
    print(f"Update: {update}")
    if 'thread_id' in update['chat']:
        thread_id = update['chat']['thread_id']
    else:
        thread_id = '0'
    if 'id' in update['chat']:
        chat_id = update['chat']['id']
    else:
        chat_id = '0'
    if 'callback_data' in update:
        callback_data = update['callback_data']
    else:
        callback_data = None

    chat = Chat(chat_id=chat_id, chat_type=update['chat']['type'], thread_id=thread_id)
    from_m = From(display_name=update['from']['display_name'],
                  from_id=update['from']['id'],
                  login=update['from']['login'],
                  robot=update['from']['robot'])
    if 'reply_to_message' in update:
        reply_to_message = create_reply_update(update['reply_to_message'])
        update = Update(chat=chat, from_m=from_m,
                        message_id=update['message_id'],
                        text=update['text'],
                        timestamp=update['timestamp'],
                        update_id=update['update_id'],
                        reply_to_message=reply_to_message,
                        callback_data=callback_data)
    else:
        update = Update(chat=chat, from_m=from_m,
                        message_id=update['message_id'],
                        text=update['text'],
                        timestamp=update['timestamp'],
                        update_id=update['update_id'],
                        callback_data=callback_data)
    return update


def start(cb_function, **kwargs):
    """
    This function starts the bot and continuously fetches updates from the Yandex 360 service.
    It uses a callback function to process each update.

    Parameters:
    cb_function (function): A callback function that will be called for each update.

    Returns:
    None
    """

    # Initial request body with limit and offset
    request_body = {'limit': 100, 'offset': 0}
    last_update_id = -1

    # Send initial request to Yandex 360 service to scip old messages
    response = post(url, json=request_body, headers=headers)
    if response.status_code == 200:
        updates = response.json()['updates']
        if len(updates) > 0:
            # Update last_update_id with the id of the last update
            last_update_id = int(updates[len(updates) - 1]['update_id'])
            print(f"Last Update Id: {last_update_id} writing to.last_update")

    else:
        print(f"Невозможно подключиться к сервису Яндекс 360: {response.status_code}")
        exit(1)

    while True:
        # Update request body with offset as last_update_id + 1
        request_body = {'limit': 100, 'offset': last_update_id + 1}
        # print(f"Request Body: {request_body}")

        # Send request to Yandex 360 service
        response = post(url, json=request_body, headers=headers)
        updates = response.json()['updates']
        if response.status_code == 200:
            if len(updates) > 0:
                # Update last_update_id with the id of the last update
                last_update_id = int(updates[len(updates) - 1]['update_id'])
                for upd in updates:
                    # Create Update object and call the callback function
                    update = create_update(upd)
                    cb_function(update, **kwargs)
            # else:
            #     print("No new updates")
        else:
            print(response.status_code)

        # Sleep for 5 seconds before making the next request
        sleep(5)
