import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

# Настройки для ChromeDriver
options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0")
options.add_argument("--disable-blink-features=AutomationControlled")

# Укажите путь к chromedriver
s = Service(executable_path="C:\\chromedriver\\chromedriver.exe")
driver = webdriver.Chrome(service=s, options=options)

try:
    driver.get("https://www.drive.ru/tires")
    time.sleep(10)  # Даем время для загрузки страницы

    articles_data = []

    # Найти все элементы с классом 'header news-item-caption'
    news_items = driver.find_elements(By.CLASS_NAME, 'news-item-caption')

    for item in news_items:
        try:
            # Извлечь категорию и дату
            category_date = item.find_element(By.CLASS_NAME, 'news-item-caption__category').text.strip()
            
            # Извлечь заголовок
            title_element = item.find_element(By.CLASS_NAME, 'news-item-caption__text')
            title = title_element.text.strip()
            
            # Извлечь ссылку
            link = title_element.find_element(By.TAG_NAME, 'a').get_attribute('href').strip()

            # Открыть статью и извлечь контент
            driver.get(link)
            time.sleep(5)  # Даем время для загрузки страницы

            try:
                # Здесь измените селектор на тот, который соответствует содержимому статьи
                content_element = driver.find_element(By.CSS_SELECTOR, '.article-content')
                content = content_element.text.strip()
            except Exception as e:
                print(f"Ошибка при извлечении контента статьи: {e}")
                content = "Контент не найден"

            # Вернуться на главную страницу с новостями
            driver.back()
            time.sleep(5)  # Даем время для загрузки страницы

            # Сохранить данные в словарь
            articles_data.append({
                'category_date': category_date,
                'title': title,
                'link': link,
                'content': content
            })
        except Exception as e:
            print(f"Ошибка при обработке элемента: {e}")

    # Конвертировать данные в JSON
    articles_json = json.dumps(articles_data, ensure_ascii=False, indent=4)
    print(articles_json)

except Exception as ex:
    print(ex)
finally:
    driver.close()
    driver.quit()
