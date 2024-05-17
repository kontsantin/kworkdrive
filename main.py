import json
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import pandas as pd

# Настройки для ChromeDriver
options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0")
options.add_argument("--disable-blink-features=AutomationControlled")

# Укажите путь к chromedriver
s = Service(executable_path="C:\\chromedriver\\chromedriver.exe")
driver = webdriver.Chrome(service=s, options=options)

def clean_markdown(text):
    """Очистка маркдауна от изображений и ссылок"""
    # Удалить изображения
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # Удалить ссылки, оставив только текст
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Заменить h-теги на маркдаун-формат
    text = re.sub(r'<h[1-6]>(.*?)<\/h[1-6]>', r'### \1', text)
    return text

def parse_article(url, driver):
    try:
        driver.get(url)
        # Даем время для загрузки страницы

        # Найти все ссылки на странице
        links = driver.find_elements(By.TAG_NAME, 'a')
        article_links = [link.get_attribute('href') for link in links if link.get_attribute('href') and link.get_attribute('href').endswith('.html')]

        initial_article_count = len(article_links)
        articles_data = []

        for link in article_links:
            try:
                # Открыть статью и извлечь контент
                driver.get(link)
                

                # Измените селектор на тот, который соответствует содержимому статьи
                title_element = driver.find_element(By.CSS_SELECTOR, '.afigure-title')
                title = title_element.text.strip()

                content_element = driver.find_element(By.CSS_SELECTOR, '.article-content')
                content_html = content_element.get_attribute('innerHTML').strip()

                # Преобразовать HTML в Markdown и очистить контент
                markdown_content = clean_markdown(md(content_html))

                # Сохранить данные в словарь
                article_data = {
                    'title': title,
                    'ArticleTextMarkdown': markdown_content,
                    'ArticleTextHTML': content_html
                }

                # Проверить на дубли
                if article_data not in articles_data and markdown_content != "Контент не найден":
                    articles_data.append(article_data)

                # Вернуться на главную страницу с новостями
                driver.back()
  

            except Exception as e:
                print(f"Ошибка при обработке элемента: {e}")

        final_article_count = len(articles_data)
        print(f"Найдено статей на странице: {initial_article_count}")
        print(f"Успешно спарсено и сохранено статей: {final_article_count}")

        return articles_data

    except Exception as e:
        print(f"Ошибка при парсинге страницы: {e}")
        return []

def save_to_json(data, filename):
    """Сохранение данных в JSON-файл"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = []

    existing_data.extend(data)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)

    print(f"Данные сохранены в файл: {filename}")

def main():
    try:
        url_file = 'urls.txt'
        json_file = 'articles_data.json'

        if not os.path.exists(url_file):
            print(f"Файл {url_file} не найден.")
            return

        with open(url_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]

        for url in urls:
            articles_data = parse_article(url, driver)
            if articles_data:
                save_to_json(articles_data, json_file)

        # Валидировать JSON-файл
        try:
            df = pd.read_json(json_file)
            print("JSON-файл сформирован корректно.")
        except ValueError as e:
            print(f"Ошибка при валидации JSON-файла: {e}")

    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()

if __name__ == "__main__":
    main()
