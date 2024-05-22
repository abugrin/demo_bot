import threading
from time import sleep

import bot_pool
from bot_api import send_message, send_inline_keyboard, send_image
from gpt_api import send_art_request, get_art_response, send_translate_request
from tracker_api import create_ticket


def my_bot(update: bot_pool.Update):
    # print(f"Received Update: {update.update_id} text: {update.text}")
    global art_queue

    if f'{update.from_m.from_id}' in pass_requests:
        button_pass_yes = {'text': 'Да', 'callback_data': {'cmd': '/pass_yes', 'name': update.text}}
        button_pass_no = {'text': 'Нет', 'callback_data': {'cmd': '/pass_no'}}
        send_inline_keyboard(f'Заказать пропуск для: {update.text}', [button_pass_yes, button_pass_no], update)
        pass_requests.pop(f'{update.from_m.from_id}', None)
    elif f'{update.from_m.from_id}' in art_requests:
        button_art_yes = {'text': 'Да', 'callback_data': {'cmd': '/art_yes', 'text': update.text}}
        button_art_no = {'text': 'Нет', 'callback_data': {'cmd': '/art_no'}}
        send_inline_keyboard(f'Сгенерировать изображение по запросу: {update.text}', [button_art_yes, button_art_no], update)
        art_requests.pop(f'{update.from_m.from_id}', None)
    elif f'{update.from_m.from_id}' in translate_requests:
        response = send_translate_request(update.text)
        text = response['translations'][0]['text']
        send_message(f"Перевод:\n```{text}```", update)
        send_menu(update)
        translate_requests.pop(f'{update.from_m.from_id}', None)
    else:
        if update.callback_data:
            # print(f"Callback Data: {update.callback_data}")
            message = update.callback_data['cmd']
        else:
            message = str.lower(update.text)

        if message == "/help":
            send_message("Напишите привет для начала", update)
            send_menu(update)
        elif message == "/hello":
            send_message('Я всё вижу', update)
            send_menu(update)
        elif message == "/start":
            send_menu(update)
        elif message == "/art":
            send_message('Введете текст для генерации изображения', update)
            art_requests.update({f'{update.from_m.from_id}': update})
        elif message == "/translate":
            send_message('Введете текст для перевода', update)
            translate_requests.update({f'{update.from_m.from_id}': update})
        elif message == "/pass":
            pass_requests.update({f'{update.from_m.from_id}': update})
            send_message("Введите имя и фамилию для заказа пропуска", update)
        elif message == "/pass_yes":
            res = create_ticket(update.callback_data['name'])
            send_message(f"Заявка на пропуск оформлена: https://tracker.yandex.ru/{res['key']}", update)
            send_menu(update)
        elif message == "/pass_no":
            send_message(f"Заказ пропуска отменен", update)
            send_menu(update)
        elif message == "/art_yes":
            response = send_art_request(update.callback_data['text'])
            print(f"Art response: {response}")
            try:
                send_message(f"Отправлен запрос на генерацию изображения. Id запроса: {response['id']}", update)
                c.acquire()
                art_queue.update({f"{response['id']}": update})
                # c.notify()
                c.release()
            except KeyError:
                send_message(f"Ошибка: {response['error']}", update)
                send_menu(update)

        elif message == "/art_no":
            send_message(f"Генерация изображения отменена", update)
            send_menu(update)
        else:
            send_menu(update)


def send_menu(update):
    send_inline_keyboard("Доступные команды:", menu_main, update)


def art_thread():
    global art_queue

    while True:
        print("Art queue size: ", len(art_queue))
        for art_request in art_queue:
            # print(f"Working on art request: {art_request}")
            response = get_art_response(art_request)
            # print(f"Art response: {response}")
            if response['done']:
                send_message("Изображение готово", art_queue[art_request])
                send_image(response['response']['image'], art_queue[art_request])
                send_menu(art_queue[art_request])
                c.acquire()
                art_queue.pop(art_request, None)
                # c.notify()
                c.release()
                break

            else:
                send_message("Генерируется...", art_queue[art_request])
        # print("Sleeping")
        sleep(10)


if __name__ == '__main__':
    c = threading.Condition()

    art_queue = {}
    pass_requests = {}
    art_requests = {}
    translate_requests = {}

    button_help = {'text': 'Помощь', 'callback_data': {'cmd': '/help'}}
    button_hello = {'text': 'Я всё вижу', 'callback_data': {'cmd': '/hello'}}
    button_art = {'text': 'Генерация изображения', 'callback_data': {'cmd': '/art'}}
    button_translate = {'text': 'Перевод', 'callback_data': {'cmd': '/translate'}}
    button_pass = {'text': 'Пропуск', 'callback_data': {'cmd': '/pass'}}
    menu_main = [button_help, button_hello, button_art, button_translate, button_pass]

    t1 = threading.Thread(target=bot_pool.start, args=(my_bot,))
    t1.daemon = True
    t1.start()

    t2 = threading.Thread(target=art_thread)
    t2.daemon = True
    t2.start()

    while True:
        sleep(1)

    # bot_pool.start(my_bot)
