import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime

# URL страницы новостей
news_url = "https://yakovlev.ru/press-centre/releases/"


# Функция для извлечения первого абзаца текста новости
def get_news_paragraph(news_link):
    response = requests.get(news_link)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Ищем первый абзац текста новости
    paragraph = soup.find('div', class_='content').find('p')
    return paragraph.get_text(strip=True) if paragraph else None


# Основная функция для парсинга страницы новостей
def parse_news():
    response = requests.get(news_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Ищем последний блок с новостью
    latest_news_block = soup.find('div', class_='content-news-box').find('a', class_='news-item')

    if latest_news_block:
        # Извлекаем ссылку, дату и текст новости
        news_link = "https://yakovlev.ru" + latest_news_block['href']
        news_date = latest_news_block.find('div', class_='news-date').get_text(strip=True)
        news_text = get_news_paragraph(news_link)

        # Генерируем уникальный ID для новости
        news_id = hash(news_link)

        # Проверяем, существует ли уже CSV файл, если нет - создаём его
        csv_exists = os.path.exists('news_data.csv')

        with open('news_data.csv', mode='a', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['id', 'date', 'paragraph']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            # Записываем заголовок столбцов, если файл создаётся впервые
            if not csv_exists:
                writer.writeheader()

            # Записываем данные новости в CSV
            writer.writerow({
                'id': news_id,
                'date': news_date,
                'paragraph': news_text
            })


# Запускаем парсер
parse_news()
