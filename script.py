import requests
import sqlite3
from os.path import isfile
from datetime import datetime
import re
import logging
import sys

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 YaBrowser/23.3.3.719 Yowser/2.5 Safari/537.36"
}


# Класс для работы с API
class AppStore:
    def __init__(self, media, country):
        self.media = media
        self.country = country

    # Метод для поиска приложений в App Store по заданному слову
    def search_app_in_itunes(self, term, limit):
        url = "https://itunes.apple.com/search"
        payload = {"term": term, "media": self.media, "country": self.country, "limit": limit}
        response = requests.get(url, params=payload)
        results = response.json().get("results", [])
        return results

    # Метод для поиска названия приложения по его apple id
    def search_app_name_by_id(self, id):
        url = "https://itunes.apple.com/lookup"
        payload = {"id": id, "media": self.media}
        response = requests.get(url, params=payload)
        results = response.json().get("results", [])
        if results != []:
            app_name = response.json()['results'][0]['trackName']
            return app_name
        else:
            logging.info(f'Information not found (appleid={id})')
            print(f'Information not found (appleid={id})')
            return sys.exit()


# Класс для работы с базой данных itunes.db
class Database:
    def __init__(self, name):
        self.name = name

    # Метод для создания базы данных и таблицы itunes
    def create_bd(self):
        conn = sqlite3.connect(self.name)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE itunes
        (id INTEGER,
        word TEXT,
        pos INTEGER,
        date DATE);''')
        conn.commit()
        conn.close()

    # Метод для добавления результатов поиска в базу данных
    def insert_into_table(self, id, word, pos, date):
        conn = sqlite3.connect(self.name)
        cur = conn.cursor()
        cur.execute(f"INSERT INTO itunes (id, word, pos, date) VALUES (?, ?, ?, ?);", (id, word, pos, date))
        conn.commit()
        conn.close()


# Функция для очистки строки от специальных символов
def clean_string(string):
    return re.sub(r'[^a-zA-Z0-9А-Яа-я\s]', '', string)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename="log_file.log",
        format="[%(asctime)s] %(module)s %(levelname)s : %(lineno)d - %(message)s"
    )

    # Запрашиваем apple id приложения у пользователя
    id = input("Enter the app's appleid:")  # Пример appleid - 860011430
    if id.isdigit():
        id = int(id)
    else:
        print(f'Appleid is not correct')
        sys.exit()

    # Получаем текущую дату и время
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Если база данных itunes.db не создана, то создаем
    db = Database('itunes.db')
    if not isfile('itunes.db'):
        db.create_bd()

    # Создаем объект
    app_store = AppStore(media="software", country="RU")

    # Получаем название приложения по его apple id
    app_name = app_store.search_app_name_by_id(id)
    app_name = clean_string(app_name)

    # Разбиваем название приложения на слова и ищем каждое слово в App Store
    app_words = app_name.split()

    for word in app_words:
        result_search = app_store.search_app_in_itunes(word, limit=200)
        result_search_list = [d['trackId'] for d in result_search if 'trackId' in d]
        pos = None

        # Если apple id приложения найден в результате поиска - добавляем его позицию в таблицу itunes
        if id in result_search_list:
            pos = result_search_list.index(id) + 1
            db.insert_into_table(id, word, pos, date)
            logging.info(f'The position search result has been added to the table (word={word})')
        else:
            db.insert_into_table(id, word, pos, date)
            logging.info(f'The position search result has not been added to the table (word={word})')

    logging.info(f"Research for {app_name} completed")
    print(f"Research for {app_name} completed")
