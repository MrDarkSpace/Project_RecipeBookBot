import requests
import json
import pandas as pd
from time import sleep


url = "https://api.telegram.org/" \
      "bot1498089964:AAEWSeqQ2uAxJo7DaOEnwHrjJbZ3xuytqqY/"
update_id = 0
# recipes = pd.DataFrame({'UserChatID': [],
#                         'Name': [], 'Products': [], 'Process': []})
recipes = pd.read_excel('recipes.xlsx')
current_index = len(recipes)
unanswered = set()


def get_updates(url):
    global update_id
    paramet = {'timeout': 200, 'offset': update_id - 50}
    response = requests.get(url + 'getUpdates', data=paramet)
    return response.json()


def last_update(data):
    res = data['result']
    num_upd = len(res) - 1
    return res[num_upd]


def get_chat_id(result):
    chat_id = result['message']['chat']['id']
    return chat_id


def send_mess(url, chat_id, mes_text, reply_markup=None):
    paramet = {'chat_id': chat_id, 'text': mes_text,
               'reply_markup': reply_markup,
               'disable_web_page_preview': 'true'}
    sending = requests.post(url + 'sendMessage', data=paramet)
    return sending


def get_new_mess(url, chat_id):
    global update_id
    counter = 0
    while True:
        last_upd = last_update(get_updates(url))
        if chat_id == get_chat_id(last_upd):
            if update_id == last_upd['update_id'] - 1:
                update_id += 1
                break
        else:
            if update_id == last_upd['update_id'] - 1:
                send_mess(url, get_chat_id(last_upd),
                          "Прости, но бот пока что занят "
                          "записыванием чужого рецепта :(")
                send_mess(url, get_chat_id(last_upd),
                          "Как только я освобожусь - "
                          "я отвечу на твой запрос!")
                global unanswered
                unanswered.add(get_chat_id(last_upd))
                update_id += 1
        sleep(1)
        counter += 1
        if counter == 100:
            send_mess(url, chat_id, "Ты куда-то пропал т-т")
            raise Exception
    if last_upd['message']['text'][0] == '/':
        update_id += 1
        raise Exception
    return last_upd['message']['text']


def menu(url, chat_id):
    reply_markup = {'keyboard': [['Создать новый рецепт'],
                                 ['Найти рецепт в Кулинарной Книге'],
                                 ['Статистика']],
                    'resize_keyboard': True,
                    'one_time_keyboard': True}
    reply_markup = json.dumps(reply_markup)
    send_mess(url, chat_id, "Сейчас ты в меню. Что ты хочешь сделать?",
              reply_markup=reply_markup)


def creating_new_recipe(url, chat_id, cur_recipes):
    send_mess(url, chat_id, "OK! Давай создадим лучшее блюдо в мире!")
    send_mess(url, chat_id, "Напиши мне название своего нового блюда.")
    global recipes
    while True:
        try:
            name = get_new_mess(url, chat_id)
        except:
            return
        if not (recipes.empty):
            if len((cur_recipes.loc[recipes.Name == name.upper()])) != 0:
                send_mess(url, chat_id,
                          "Блюдо с таким названием уже есть "
                          "в базе! Придумай что-то оригинальное!")
            else:
                break
        else:
            break
    send_mess(url, chat_id, "OK! Теперь напиши мне "
                            "список продуктов через запятую :)")
    try:
        products = get_new_mess(url, chat_id)
    except:
        return
    send_mess(url, chat_id, "Надеюсь, что ты ничего не забыл! "
                            "Теперь пришло время описать "
                            "процесс приготовления одним сообщением")
    try:
        process = get_new_mess(url, chat_id)
    except:
        return
    global current_index
    recipes.loc[current_index] = [chat_id, name.upper(),
                                  products.upper(), process]
    current_index += 1
    send_mess(url, chat_id, "Рецепт добавлен! Возвращаемся в меню.")


def search_recipe(url, chat_id, cur_recipes):
    global recipes
    while True:
        reply_markup = {'keyboard': [['По названию'],
                                     ['По составу'], ['Меню']],
                        'resize_keyboard': True,
                        'one_time_keyboard': True}
        reply_markup = json.dumps(reply_markup)
        send_mess(url, chat_id, "Как ты хочешь найти блюдо?",
                  reply_markup=reply_markup)
        try:
            answ = get_new_mess(url, chat_id)
        except:
            return
        if answ == 'По названию':
            send_mess(url, chat_id, "Введи название:")
            try:
                name = get_new_mess(url, chat_id)
            except:
                return
            find = cur_recipes.loc[cur_recipes.Name == name.upper()]
            if len(find) != 0:
                send_mess(url, chat_id, find.Name)
                send_mess(url, chat_id, find.Products)
                send_mess(url, chat_id, find.Process)
                reply_markup = {'keyboard': [['Удалить рецепт'],
                                             ['Редактировать рецепт'],
                                             ['Меню']],
                                'resize_keyboard': True,
                               'one_time_keyboard': True}
                reply_markup = json.dumps(reply_markup)
                send_mess(url, chat_id, "Если хочешь, "
                                        "то можно удалить рецепт. "
                                        "Или просто вернемся в меню :)",
                          reply_markup=reply_markup)
                try:
                    com = get_new_mess(url, chat_id)
                except:
                    return
                if com == "Удалить рецепт":
                    recipes = recipes.drop(find.index)
                    send_mess(url, chat_id, "Успешно удалено!")
                elif com == "Редактировать рецепт":
                    reply_markup = {'keyboard':
                                        [['Редактировать название'],
                                         ['Редактировать состав'],
                                         ['Редактировать описание'],
                                         ['Меню']],
                                    'resize_keyboard': True,
                                    'one_time_keyboard': True}
                    reply_markup = json.dumps(reply_markup)
                    send_mess(url, chat_id, "Что именно ты хотел бы "
                                            "отредактировать?",
                              reply_markup=reply_markup)
                    try:
                        new_com = get_new_mess(url, chat_id)
                    except:
                        return
                    if new_com == 'Редактировать название':
                        send_mess(url, chat_id, "Введи новое название:")
                        try:
                            new_name = get_new_mess(url, chat_id)
                        except:
                            return
                        recipes.loc[find.index, 'Name'] = new_name.upper()
                    elif new_com == 'Редактировать состав':
                        send_mess(url, chat_id, "Введи новый состав:")
                        try:
                            new_products = get_new_mess(url, chat_id)
                        except:
                            return
                        recipes.loc[find.index, 'Products'] = \
                            new_products.upper()
                    elif new_com == 'Редактировать состав':
                        send_mess(url, chat_id, "Введи новый "
                                                "процесс приготовления:")
                        try:
                            new_process = get_new_mess(url, chat_id)
                        except:
                            return
                        recipes.loc[find.index, 'Process'] = new_process
                    elif new_com == 'Меню':
                        pass
                    else:
                        send_mess(url, chat_id, "К сожалению, "
                                                "я ничего не понял :( "
                                                "Вернусь в меню")
            else:
                send_mess(url, chat_id, "Не могу найти такой рецепт :(")
            break
        elif answ == 'По составу':
            cur_df = pd.DataFrame(columns=recipes.columns)
            send_mess(url, chat_id, "Введи все необходимые ингридиенты "
                                    "через запятую.")
            try:
                prod = get_new_mess(url, chat_id).upper().split(', ')
            except:
                return
            for i in range(current_index):
                err = 0
                for j in range(len(prod)):
                    if recipes.iloc[i]['Products'].find(prod[j]) != -1 \
                            and recipes.iloc[i]['UserChatID'] == chat_id:
                        pass
                    else:
                        err = -1
                        break
                if err == 0:
                    cur_df = cur_df.append(recipes.iloc[i])
            if len(cur_df) != 0:
                send_mess(url, chat_id, "Я нашел {} вариантов. "
                                        "Сейчас покажу все "
                                        "названия:".format(len(cur_df)))
                mes = ''
                if len(cur_df) != 1:
                    for j in range(len(cur_df)):
                        mes += str(cur_df.iloc[j]['Name']) + '\n'
                else:
                    mes = str(cur_df.iloc[0]['Name'])
                send_mess(url, chat_id, mes)
                send_mess(url, chat_id, "Введи название:")
                try:
                    name = get_new_mess(url, chat_id)
                except:
                    return
                find = cur_recipes.loc[cur_recipes.Name == name.upper()]
                if len(find) != 0:
                    send_mess(url, chat_id, find.Name)
                    send_mess(url, chat_id, find.Products)
                    send_mess(url, chat_id, find.Process)
                else:
                    send_mess(url, chat_id, "Не могу найти такой "
                                            "рецепт :(")

            else:
                send_mess(url, chat_id, "Нет рецептов с таким "
                                        "составом :(")
            break
        elif answ == 'Меню':
            break
        else:
            send_mess(url, chat_id, "Не понимаю :(")


def main():
    global update_id
    update_id = last_update(get_updates(url))['update_id']
    while True:
        if update_id == last_update(get_updates(url))['update_id']:
            last_upd = last_update(get_updates(url))
            chat_id = get_chat_id(last_update(get_updates(url)))
            cur_recipes = recipes.loc[recipes.UserChatID == chat_id]

            if last_upd['message']['text'] == '/start':
                send_mess(url, chat_id, "Привет!")
                send_mess(url, chat_id, "Я специальный бот для ведения твоей "
                                        "личной кулинарной книги!")
                menu(url, chat_id)
            elif last_upd['message']['text'] == '/menu':
                menu(url, chat_id)
            elif last_upd['message']['text'] == 'Создать новый рецепт':
                creating_new_recipe(url, chat_id, cur_recipes)
                menu(url, chat_id)
            elif last_upd['message']['text'] == 'Найти рецепт в ' \
                                                'Кулинарной Книге':
                search_recipe(url, chat_id, cur_recipes)
                menu(url, chat_id)
            elif last_upd['message']['text'] == 'Статистика':
                send_mess(url, chat_id, "У тебя в Кулинарной книге {} "
                                        "рецептов!".format(len(cur_recipes)))
                menu(url, chat_id)

            update_id += 1
        elif update_id < last_update(get_updates(url))['update_id']:
            update_id = last_update(get_updates(url))['update_id']
        sleep(1)
        recipes.to_excel('recipes.xlsx', index=False)
        if len(unanswered) != 0:
            for i in range(len(unanswered)):
                send_mess(url, unanswered.pop(), 'Я освободился!')


if __name__ == '__main__':
    main()
