from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import time
import pymysql


chrome_driver_path = r"C:\Users\李震彬\Downloads\chromedriver-win32\chromedriver-win32\chromedriver.exe"


chrome_options = Options()
chrome_options.add_argument("--headless")  

service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)


url = "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=B0000001"


driver.get(url)


time.sleep(10)

html = driver.page_source

soup = BeautifulSoup(html, 'html.parser')

def get_conn():  
    return pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="00000000",
        database="python_mysql",
        charset="utf8"
    )

connection = get_conn()  
cursor = connection.cursor()

law_sections = soup.find_all('div', class_='law-article')

if law_sections:
    for section in law_sections:

        article_number = section.find_previous('div', class_='col-no')
        if article_number:
            article_number_text = article_number.get_text(strip=True)
        else:
            article_number_text = "未知條號"

      
        law_text_combined = []

        paragraphs = section.find_all(['p', 'div', 'span'])
        for paragraph in paragraphs:
            text = paragraph.get_text()
            if text:
                # 保留中文字符、數字和標點符號
                chinese_numbers_punctuation_text = re.sub(r'[^\u4e00-\u9fff0-9。，、？！：；「」『』《》〈〉（）〔〕—－,."\'!?;:()【】[\]{}<>]+', ' ', text)
                if chinese_numbers_punctuation_text.strip():
                    law_text_combined.append(chinese_numbers_punctuation_text)

       
        if law_text_combined:
            combined_text = ' '.join(law_text_combined)

            
            sql = "INSERT INTO civil_law (article_number, law_content) VALUES (%s, %s)"
            cursor.execute(sql, (article_number_text, combined_text))


connection.commit()

cursor.close()
connection.close()


driver.quit()

