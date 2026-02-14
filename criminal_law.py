import os
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import time
import sqlite3

def setup_chrome_driver():
    """Configure Chrome WebDriver with options to reduce errors"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-ssl-errors=yes")
    chrome_options.add_argument("--ignore-certificate-errors")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def chunk_law_text(full_text):
    """Split full law text into laws_full, laws_part, laws_sent"""
    sentences = re.split(r'[。？！]', full_text)
    laws_full = full_text
    laws_part = sentences[0] if sentences else ""
    laws_sent = sentences[1] if len(sentences) > 1 else ""
    return laws_full, laws_part, laws_sent

def clean_text(text):
    """Clean and filter text content"""
    cleaned_text = re.sub(r'[^\u4e00-\u9fff0-9。，、？！：；「」『』《》〈〉（）〔〕—－,."\'!?;:()\[\]\{\}<>]+', ' ', text)
    return cleaned_text.strip()

def scrape_law_sections(driver, url):
    """Scrape law sections with proper ordering"""
    driver.get(url)
    
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'law-article'))
    )
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    law_sections = soup.find_all('div', class_='law-article')

    sorted_sections = []
    for section in law_sections:

        article_number = section.find_previous('div', class_='col-no')
        if article_number:
            try:
                number = int(re.findall(r'\d+', article_number.get_text(strip=True))[0])
                sorted_sections.append((number, section))
            except (IndexError, ValueError):
                sorted_sections.append((float('inf'), section))
    sorted_sections.sort(key=lambda x: x[0])
    
    return sorted_sections

def main():
    url = "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=C0000001"
    
    driver = setup_chrome_driver()
    
    try:
        sorted_law_sections = scrape_law_sections(driver, url)
        
        law_db_path = "law.db"
        connection = sqlite3.connect(law_db_path)
        cursor = connection.cursor()
    
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emp (
                article_number INTEGER,
                laws_full TEXT NOT NULL,
                laws_part TEXT NOT NULL,
                laws_sent TEXT NOT NULL
            )
        ''')

        for index, (article_number, section) in enumerate(sorted_law_sections, 1):

            law_text_combined = []
            paragraphs = section.find_all(['p', 'div', 'span'])
            
            for paragraph in paragraphs:
                text = paragraph.get_text()
                if text:
                    cleaned_text = clean_text(text)
                    if cleaned_text:
                        law_text_combined.append(cleaned_text)
            
            if law_text_combined:
                combined_text = ' '.join(law_text_combined)

                laws_full, laws_part, laws_sent = chunk_law_text(combined_text)

                sql = "INSERT INTO emp (article_number, laws_full, laws_part, laws_sent) VALUES (?, ?, ?, ?)"
                cursor.execute(sql, (index, laws_full, laws_part, laws_sent))
        
        connection.commit()
        
        with open("lawsql.sql", "w", encoding="utf-8") as sql_file:
            for line in connection.iterdump():
                sql_file.write('%s\n' % line)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()
        
        driver.quit()

if __name__ == "__main__":
    main()