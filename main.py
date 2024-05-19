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
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'<h[1-6]>(.*?)<\/h[1-6]>', r'### \1', text)
    return text

def parse_article(url, driver, max_articles=500):
    articles_data = []
    parsed_titles = set()

    try:
        driver.get(url)
       

        while len(articles_data) < max_articles:
            # Получаем все статьи на странице
            links = driver.find_elements(By.TAG_NAME, 'a')
            article_links = [link.get_attribute('href') for link in links if link.get_attribute('href') and link.get_attribute('href').endswith('.html')]
            article_links = list(set(article_links))  # Убираем дублирующиеся ссылки

            for article_link in article_links:
                if len(articles_data) >= max_articles:
                    break

                # Открываем статью в новой вкладке
                driver.execute_script("window.open(arguments[0], '_blank');", article_link)
                driver.switch_to.window(driver.window_handles[-1])
                

                try:
                    title_element = driver.find_element(By.CSS_SELECTOR, '.afigure-title')
                    title = title_element.text.strip()

                    if title in parsed_titles:
                        driver.close()  # Закрываем вкладку с текущей статьей
                        driver.switch_to.window(driver.window_handles[0])  # Переключаемся обратно на основную вкладку
                        continue

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

                    if markdown_content != "Контент не найден":
                        articles_data.append(article_data)
                        parsed_titles.add(title)

                except Exception as e:
                    print(f"Ошибка при обработке элемента: {e}")
                finally:
                    driver.close()  # Закрываем вкладку с текущей статьей
                    driver.switch_to.window(driver.window_handles[0])  # Переключаемся обратно на основную вкладку

            # Проверяем наличие кнопки "Показать еще"
            try:
                button = driver.find_element(By.ID, 'show-more-link')
                driver.execute_script("arguments[0].click();", button)
                time.sleep(5)  # Даем время для загрузки дополнительных статей
            except Exception as e:
                print("Кнопка 'Показать еще' не найдена или произошла ошибка: ", e)
                break  # Если кнопка не найдена или произошла ошибка, выходим из цикла

        final_article_count = len(articles_data)
        print(f"Успешно спарсено и сохранено статей: {final_article_count}")

    except Exception as e:
        print(f"Ошибка при парсинге страницы: {e}")

    return articles_data

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
