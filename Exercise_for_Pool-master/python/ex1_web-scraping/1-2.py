import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import re
import time
import traceback

# ChromeDriverのURL
CHROMEDRIVER_URL = "https://github.com/MikaHayakawa0930/Final_Answer/raw/main/Exercise_for_Pool-master/python/ex1_web-scraping/chromedriver.exe"

# 一時ディレクトリにダウンロード
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
options = Options()
options.add_argument('--headless')  # ヘッドレスモード
options.add_argument('--ignore-ssl-errors')
options.add_argument('--disable-web-security')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

service = Service(CHROME_DRIVER_PATH)

# WebDriverを初期化
driver = webdriver.Chrome(service=service, options=options)

# データ格納リスト
data = []

# ベースURL
BASE_URL = 'https://r.gnavi.co.jp/eki/0006423/rs/'

def extract_store_details():
    try:
        # 最初のページを開く
        driver.get(BASE_URL)
        time.sleep(3)  # 初期ページ読み込み待機

        max_records = 50  # 最大レコード数
        records_collected = 0  # 現在収集したレコード数

        current_page = 1

        while records_collected < max_records:
            print(f"現在のページURL: {driver.current_url}")

            # 現在のページの店舗リンクを取得
            try:
                store_links = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.style_titleLink__oiHVJ'))
                )
                links = [link.get_attribute('href') for link in store_links if link.get_attribute('href')]
                print(f"取得したリンク数: {len(links)}")
            except TimeoutException:
                print("店舗リンクの取得に失敗しました。")
                break

            # 各店舗の詳細ページを処理
            for link in links:
                if records_collected >= max_records:
                    break
                try:
                    print(f"処理中: {link}")
                    driver.get(link)
                    time.sleep(3)  # ページ遷移のための待機

                    # 店舗名
                    store_name = driver.find_element(By.CSS_SELECTOR, 'h1').text.strip()

                    # 電話番号
                    try:
                        phone_number = driver.find_element(By.CSS_SELECTOR, 'span.number').text.strip()
                    except NoSuchElementException:
                        phone_number = ''

                    # 住所
                    try:
                        address_element = driver.find_element(By.CSS_SELECTOR, 'p.adr').text.strip()
                        address_element = re.sub(r'〒?\d{3}-\d{4}', '', address_element).strip()
                        match = re.match(r'^(.*?[都道府県])(.*?[市区町村])(.*)$', address_element)
                        if match:
                            prefecture, city, rest_address = match.groups()
                            street, building = (rest_address.split(' ', 1) + [''])[:2]
                        else:
                            prefecture, city, street, building = '', '', '', ''
                    except NoSuchElementException:
                        prefecture, city, street, building = '', '', '', ''

                    # URLとSSL
                    try:
                        official_url_element = driver.find_element(By.CSS_SELECTOR, "a.url.go-off")
                        if official_url_element:
                            official_url_element.click()
                            time.sleep(3)  # URLが遷移するまで待機
                            official_url = driver.current_url.strip()
                            ssl = official_url.startswith("https://")
                        else:
                            official_url, ssl = '', False
                    except NoSuchElementException:
                        official_url, ssl = '', False

                    # データ保存
                    data.append({
                        "店舗名": store_name,
                        "電話番号": phone_number,
                        "メールアドレス": '',
                        "都道府県": prefecture,
                        "市区町村": city,
                        "番地": street,
                        "建物名": building,
                        "URL": official_url,
                        "SSL": ssl
                    })
                    records_collected += 1

                except Exception as e:
                    print(f"詳細ページの処理中にエラーが発生しました: {e}")
                    traceback.print_exc()

            if records_collected >= max_records:
                print("最大レコード数に達しました。処理を終了します。")
                break

            # 次のページURLを生成
            next_page_url = f"{BASE_URL}?p={current_page + 1}"
            print(f"次のページを試みます: {next_page_url}")

            try:
                driver.get(next_page_url)
                time.sleep(3)  # ページ遷移待機
                current_page += 1

            except Exception as e:
                print(f"次のページへの遷移中にエラーが発生しました: {e}")
                break

    except Exception as e:
        print(f"[全体エラー] エラーが発生しました: {e}")
        traceback.print_exc()

    finally:
        # データフレームに変換して保存
        df = pd.DataFrame(data)
        df.to_csv('1-2.csv', index=False, encoding='utf-8-sig')
        print("データが 1-2.csv に保存されました。")
        driver.quit()

# 実行
extract_store_details()