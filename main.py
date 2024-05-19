import json
import re
import os
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException
import time
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import pandas as pd
from datetime import datetime
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

def extract_domain(url):
    """Извлечение домена из URL"""
    parsed_url = urlparse(url)
    return parsed_url.netloc

def parse_article(url, driver, max_articles=1):
    articles_data = []
    parsed_titles = set()

    try:
        driver.get(url)
      

        while True:
            # Получаем все статьи на странице
            article_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*=".html"]')
            article_links = [element.get_attribute('href') for element in article_elements]
            article_links = list(dict.fromkeys(article_links))  # Убираем дублирующиеся ссылки

            for article_link in article_links:
                if max_articles is not None and len(articles_data) >= max_articles:
                    print(f"Достигнуто максимальное количество статей: {max_articles}. Парсинг завершен.")
                    return articles_data

                # Открываем статью в новой вкладке
                driver.execute_script("window.open(arguments[0], '_blank');", article_link)
                driver.switch_to.window(driver.window_handles[-1])
               

                try:
                    title_element = driver.find_element(By.CSS_SELECTOR, '.afigure-title h1.summary span')
                    title = title_element.text.strip()

                    if title in parsed_titles:
                        driver.close()  # Закрываем вкладку с текущей статьей
                        driver.switch_to.window(driver.window_handles[0])  # Переключаемся обратно на основную вкладку
                        continue

                    content_element = driver.find_element(By.CSS_SELECTOR, '.article-content')
                    content_html = content_element.get_attribute('innerHTML').strip()

                    # Преобразовать HTML в Markdown и очистить контент
                    content_markdown = clean_markdown(md(content_html))

                    # Извлечь дополнительные данные
                    domain = extract_domain(article_link)
                    try:
                        content_type = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:type"]').get_attribute('content')
                    except NoSuchElementException:
                        content_type = 'unknown'

                    try:
                        meta_element = driver.find_element(By.CSS_SELECTOR, '.meta')
                        time_elements = meta_element.find_elements(By.TAG_NAME, 'time')
                        for time_element in time_elements:
                            publication_date = time_element.text.strip()
                            break
                    except NoSuchElementException:
                        publication_date = 'unknown'



                    h1 = title
                    lead_element = driver.find_element(By.CSS_SELECTOR, '.afigure-caption p') if driver.find_elements(By.CSS_SELECTOR, '.afigure-caption p') else None
                    lead_html = lead_element.get_attribute('innerHTML') if lead_element else ''
                    lead_markdown = clean_markdown(md(lead_html))

                    content_element = driver.find_element(By.CSS_SELECTOR, '.article-content')
                    content_html = content_element.get_attribute('innerHTML').strip()
                    content_markdown = clean_markdown(md(content_html))
                    author = driver.find_element(By.CSS_SELECTOR, '.meta .reviewer a').text.strip() if driver.find_elements(By.CSS_SELECTOR, '.meta .reviewer a') else ''

                    # Сохранить данные в словарь
                    article_data = {
                        'domain': domain,
                        'url': article_link,
                        'content_type': content_type,
                        'publication_date': publication_date,
                        'title': title,
                        'h1': h1,
                        'lead_html': lead_html,
                        'lead_markdown': lead_markdown,
                        'content_html': content_html,
                        'content_markdown': content_markdown,
                        'author': author,
                    }

                    if content_markdown != "Контент не найден":
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
            except NoSuchElementException:
                print("Кнопка 'Показать еще' не найдена. Проверяем пагинацию.")
                try:
                    paginator = driver.find_element(By.CLASS_NAME, 'paginator')
                    next_page_link = paginator.find_element(By.XPATH, './a[contains(text(), "Вперед")]')
                    next_page_link.click()
                    time.sleep(5)  # Даем время для загрузки следующей страницы
                except NoSuchElementException:
                    print("Пагинация не найдена. Парсинг завершен.")
                    break  # Если кнопка "Вперед" не найдена, выходим из цикла пагинации
                except ElementNotInteractableException as e:
                    print(f"Кнопка 'Вперед' не может быть нажата: {e}")
                    break
                
        final_article_count = len(articles_data)
        print(f"Успешно спарсено и сохранено статей: {final_article_count}")

    except Exception as e:
        print(f"Ошибка при парсинге страницы: {e}")

    return articles_data

def save_to_json(data, filename):
    """Сохранение данных в JSON-файл"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
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
        driver.quit()

if __name__ == "__main__":
    main()
