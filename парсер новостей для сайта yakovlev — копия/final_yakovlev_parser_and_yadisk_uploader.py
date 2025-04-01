import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import json
import urllib3

# --- Функция для отправки уведомления в Telegram ---
def send_telegram_message(message):
    bot_token = 'YOUR_BOT_TOKEN'
    chat_id = 'YOUR_CHAT_ID'
    send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={message}'
    response = requests.get(send_text)
    return response.json()

# --- Парсер новостей ---
URL = "https://yakovlev.ru/press-centre/releases/"
CSV_FILE_PATH = r"D:\Python_and_Jupiter_notebooks\мой проект с акциями\csv tables\yakovlev_news_data.csv"

# Отключение предупреждений о небезопасном соединении
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Функция для проверки наличия новости в CSV (по ссылке, дате и содержанию)
def is_news_already_saved(news_link, news_date, news_summary):
    # Если файл не существует или пустой, возвращаем False
    if not os.path.exists(CSV_FILE_PATH) or os.stat(CSV_FILE_PATH).st_size == 0:
        print("Файл CSV не существует или пустой. Новость считается новой.")
        return False
    
    # Читаем CSV файл
    df = pd.read_csv(CSV_FILE_PATH)
    print(f"Проверяем таблицу:\n{df}")

    # Если нет данных в таблице (файл пустой), возвращаем False
    if df.empty:
        print("Таблица пуста. Новость считается новой.")
        return False
    
    print(f"Проверяем новость: дата = {news_date}, ссылка = {news_link}, заголовок = {news_summary}")
    
    # Проверяем, существует ли новость с таким же link, date и summary
    if news_link in df['link'].values:
        existing_news = df[df['link'] == news_link]
        print(f"Найдена новость с такой ссылкой: {existing_news}")
        
        if news_date in existing_news['date'].values and news_summary in existing_news['summary'].values:
            print("Новость найдена в таблице.")
            return True
    
    print("Новость не найдена в таблице.")
    return False

# Функция для парсинга последней новости
def parse_latest_news():
    response = requests.get(URL, verify=False)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "lxml")

        # Получаем первую новость
        latest_news = soup.find("a", class_="news-item")

        # Извлекаем ссылку, дату и заголовок
        news_link = latest_news.get("href", "")
        date_element = latest_news.find("div", class_="news-item_date")
        news_date = date_element.text.strip() if date_element else "Не указано"
        title_element = latest_news.find("div", class_="news-item_name")
        news_summary = title_element.text.strip() if title_element else "Нет заголовка"

        # Проверяем, если новость в CSV
        if not is_news_already_saved(news_link, news_date, news_summary):
            # Добавляем новость в CSV, если её там нет
            news_data = [(news_date, news_link, news_summary)]
            df = pd.DataFrame(news_data, columns=["date", "link", "summary"])

            # Сохраняем или добавляем к существующему CSV
            if os.path.exists(CSV_FILE_PATH):
                df.to_csv(CSV_FILE_PATH, mode="a", header=False, index=False, encoding="utf-8")
            else:
                df.to_csv(CSV_FILE_PATH, index=False, encoding="utf-8")
            print(f"Новая новость добавлена: {news_summary}")
            return True  # Новость была добавлена
        else:
            print("Новость уже сохранена.")
            return False  # Новость уже существует
    else:
        print(f"Ошибка при подключении: {response.status_code}")
        return False

# --- Загрузка файла на Yandex Disk ---
# Загружаем токен из файла
with open(r'D:\Python_and_Jupiter_notebooks\мой проект с акциями\yandex_token.json', 'r', encoding='utf-8') as token_file:
    token = json.load(token_file)

# Берём access_token для авторизации
access_token = token['access_token']

# Функция для загрузки файла на Яндекс Диск
def upload_to_yandex_disk(file_path, yandex_disk_path):
    headers = {
        'Authorization': f'OAuth {access_token}'.encode('utf-8')
    }

    # URL для получения ссылки на загрузку файла
    upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'

    # Параметры запроса: путь на Яндекс Диске и перезапись, если файл уже существует
    params = {
        'path': yandex_disk_path,  # Путь на Яндекс Диске
        'overwrite': 'true'  # Перезапись, если файл уже существует
    }

    # Получаем ссылку для загрузки файла
    response = requests.get(upload_url, headers=headers, params=params)

    if response.status_code == 200:
        href = response.json()['href']
        # Открываем файл и отправляем его на сервер
        with open(file_path, 'rb') as f:
            upload_response = requests.put(href, files={'file': f})

        if upload_response.status_code == 201:
            print(f"Файл {file_path} успешно загружен на Яндекс Диск: {yandex_disk_path}")
            send_telegram_message(f"Файл {file_path} успешно загружен на Яндекс Диск. ОАК Яковлев.")
        else:
            print(f"Ошибка при загрузке файла на Яндекс Диск: {upload_response.status_code}")
            send_telegram_message(f"Ошибка при загрузке файла на Яндекс Диск: {upload_response.status_code}. ОАК Яковлев.")
            print(f"Ответ сервера: {upload_response.text}")
    else:
        print(f"Ошибка при получении ссылки для загрузки файла на Яндекс Диск: {response.status_code}")
        send_telegram_message(f"Ошибка при получении ссылки для загрузки файла на Яндекс Диск: {response.status_code}. ОАК Яковлев.")
        print(f"Ответ сервера: {response.text}")

# --- Основной блок программы ---
# 1. Запускаем парсер
news_added = parse_latest_news()

# Уведомляем в Telegram о результате парсинга
if news_added:
    send_telegram_message("Новая новость успешно добавлена в CSV файл ОАК Яковлев.")
else:
    send_telegram_message("Новость уже была сохранена в CSV файле ОАК Яковлев.")

# 2. Если новость была добавлена, загружаем CSV файл на Яндекс Диск
if news_added:
    csv_file_path = CSV_FILE_PATH
    yandex_disk_file_path = '/csv files from parsers/yakovlev_news_data.csv'
    upload_to_yandex_disk(csv_file_path, yandex_disk_file_path)

    # Уведомляем о завершении загрузки
    send_telegram_message("CSV файл ОАК Яковлев успешно загружен на Яндекс Диск.")
else:
    send_telegram_message("Загрузка нового CSV файла ОАК Яковлев не требовалась.")