import base64
import os

from requests import post

from bot_pool import Update

url = "https://botapi.messenger.yandex.net/bot/v1"
headers = {
    "Authorization": f"OAuth {os.getenv('BOT_KEY')}",
    "ContentType": "application/json"
}


def send_text(body, update: Update):
    path = url + "/messages/sendText/"

    if update.chat.chat_type == 'group':
        if update.chat.thread_id != '0':
            body.update({'chat_id': update.chat.chat_id, 'thread_id': update.chat.thread_id})
        else:
            body.update({'chat_id': update.chat.chat_id})
    else:
        body.update({'login': update.from_m.login})

    response = post(path, json=body, headers=headers)
    return response.status_code


def send_message(text, update: Update):
    body = {'text': text, 'disable_web_page_preview': True}
    return send_text(body, update)


def send_inline_keyboard(text, buttons: [], update: Update):
    body = {'text': text, 'inline_keyboard': buttons}
    return send_text(body, update)


def send_image(image, update: Update):
    path = url + "/messages/sendImage/"
    header = {
        "Authorization": f"OAuth {os.getenv('BOT_KEY')}",
        "ContentType": "application/json"
    }
    img_data = base64.b64decode(image)
    files = [('image', ('image.jpeg', img_data, 'image/jpeg'))]
    body = {'login': update.from_m.login}

    response = post(path, headers=header, files=files, data=body)
    print(f"Response: {response.json()}")
