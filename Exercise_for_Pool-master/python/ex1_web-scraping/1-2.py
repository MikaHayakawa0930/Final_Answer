import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import pandas as pd
import re
import time

# ChromeDriverのダウンロードURL
CHROMEDRIVER_URL = "https://github.com/MikaHayakawa0930/Final_Answer/raw/main/Exercise_for_Pool-master/python/ex1_web-scraping/chromedriver.exe"

# ChromeDriverをダウンロード
def download_chromedriver(url):
    chromedriver_path = os.path.join(os.getcwd(), "chromedriver.exe")
    if not os.path.exists(chromedriver_path):
        print("ChromeDriverをダウンロードしています...")
        response = requests.get(url)
        with open(chromedriver_path, "wb") as file:
            file.write(response.content)
        print("ChromeDriverのダウンロードが完了しました。")
    else:
        print("既にChromeDriverが存在します。")
    return chromedriver_path

# ChromeDriverのパス
CHROME_DRIVER_PATH = download_chromedriver(CHROMEDRIVER_URL)

# Seleniumの設定
def initialize_driver():
    options = Options()
    options.add_argument('--headless')  # デバッグ時にはコメントアウト
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument("--ignore-certificate-errors")  # SSL証明書エラーを無視
    options.add_argument("--allow-insecure-localhost")   # ローカルホストの場合も許可
    options.add_argument("--disable-web-security")       # セキュリティ機能を一部無効化

    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    service = Service(CHROME_DRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)

driver = initialize_driver()

# データ格納リスト
data = []

# 店舗データの抽出関数
def extract_store_details():
    global driver
    BASE_URL = 'https://r.gnavi.co.jp/eki/0006423/rs/'

    try:
        driver.get(BASE_URL)
        time.sleep(3)

        max_records = 50
        records_collected = 0
        next_page = 2

        while records_collected < max_records:
            print(f"現在のページURL: {driver.current_url}")

            try:
                store_links = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.style_titleLink__oiHVJ'))
                )
                links = [link.get_attribute('href') for link in store_links if link.get_attribute('href')]
                print(f"取得したリンク数: {len(links)}")
            except TimeoutException:
                print("店舗リンクの取得に失敗しました。")
                break

            for link in links:
                if records_collected >= max_records:
                    break
                try:
                    print(f"処理中: {link}")
                    driver.get(link)
                    time.sleep(3)

                    store_name = driver.find_element(By.CSS_SELECTOR, 'h1').text.strip()

                    try:
                        phone_number = driver.find_element(By.CSS_SELECTOR, 'span.number').text.strip()
                    except NoSuchElementException:
                        phone_number = ''

                    try:
                        address_element = driver.find_element(By.CSS_SELECTOR, 'p.adr').text.strip()
                        address_element = re.sub(r'（エリア：.+?）$', '', address_element).strip()
                        address_element = re.sub(r'〒?\d{3}-\d{4}', '', address_element).strip()
                        match = re.match(r'^(.*?[都道府県])(.*?[市区町村])(.*)$', address_element)
                        if match:
                            prefecture, city, rest_address = match.groups()
                            street, building = (rest_address.split(' ', 1) + [''])[:2]
                        else:
                            prefecture, city, street, building = '', '', '', ''
                    except NoSuchElementException:
                        prefecture, city, street, building = '', '', '', ''

                    try:
                        # 「お店のホームページ」のリンク要素を取得
                        official_url_element = driver.find_element(By.CSS_SELECTOR, "a.url.go-off")
    
                        # href属性からURLを直接取得
                        official_url = official_url_element.get_attribute("href").strip()
    
                        # SSL（https対応かどうか）の確認
                        ssl = official_url.startswith("https://")
                    except NoSuchElementException:
                        official_url, ssl = '', False
                        
                    try:
                        email_element = driver.find_element(By.CSS_SELECTOR, "a[href^='mailto']")
                        email_address = email_element.get_attribute('href').replace('mailto:', '').strip()
                    except NoSuchElementException:
                        email_address = ''

                    data.append({
                        "店舗名": store_name,
                        "電話番号": phone_number,
                        "メールアドレス": email_address,
                        "都道府県": prefecture,
                        "市区町村": city,
                        "番地": street,
                        "建物名": building,
                        "URL": official_url,
                        "SSL": ssl
                    })
                    records_collected += 1
                    driver.back()

                except Exception as e:
                    print(f"詳細ページの処理中にエラーが発生しました: {e}")

            try:
                current_url = driver.current_url
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f'a[href*="rs/?p={next_page}"]'))
                )
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(3)

                WebDriverWait(driver, 10).until(EC.url_changes(current_url))
                next_page += 1

            except TimeoutException:
                print("次ページボタンが見つかりません。終了します。")
                break

    except WebDriverException as e:
        if "disconnected" in str(e):
            print("ブラウザ接続エラー。ドライバを再起動します。")
            driver.quit()
            driver = initialize_driver()
        else:
            print(f"全体エラーが発生しました: {e}")

    finally:
        df = pd.DataFrame(data)
        df.to_csv('1-2.csv', index=False, encoding='utf-8-sig')
        print("データが 1-2.csv に保存されました。")
        driver.quit()

# 実行
extract_store_details()
