from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re
import time
import traceback

# ChromeDriverの設定
chrome_service = Service(executable_path=r"C:\Users\mh9iy\OneDrive\お仕事\chromedriver-win64\chromedriver.exe")
chrome_options = Options()
chrome_options.add_argument('--headless')  # ヘッドレスモード
chrome_options.add_argument('--ignore-ssl-errors')  # SSLエラーを無視
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

# データ格納リスト
data = []

# ベースURL
BASE_URL = 'https://r.gnavi.co.jp/eki/0006423/rs/'
driver.get(BASE_URL)

def extract_details(detail_url):
    # 店舗詳細ページから情報を抽出する関数
    driver.get(detail_url)
    time.sleep(3)  # ページ読み込みのため待機

    try:
        # 店舗名を取得
        store_name = driver.find_element(By.CSS_SELECTOR, 'h1').text.strip()
    except Exception:
        store_name = ''

    try:
        # 電話番号を取得
        phone_number = driver.find_element(By.CSS_SELECTOR, 'tr#info-phone span.number').text.strip()
    except Exception:
        phone_number = ''

    email = ''  # メールアドレスは通常存在しないため空欄にする

    try:
        # 住所を取得し分割
        address_element = driver.find_element(By.CSS_SELECTOR, 'p.adr').text.strip()

        # 郵便番号と「〒」を除去
        address_element = re.sub(r'〒?\d{3}-\d{4}', '', address_element).strip()

        # 正規表現で住所を分割
        pattern = re.compile(r'^(.*?[都道府県])(.*?[市区町村])(.*)$')
        match = pattern.match(address_element)
        if match:
            prefecture, city, rest_address = match.groups()
            # 番地と建物名を分割（スペースが無い場合の対応も追加）
            parts = rest_address.split(' ', 1)
            street = parts[0]
            building = parts[1] if len(parts) > 1 else ''
        else:
            prefecture, city, street, building = '', '', '', ''
    except Exception:
        prefecture, city, street, building = '', '', '', ''

    try:
        # URLとSSL確認
        official_url_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'tr#info-url a'))
        )
        official_url = official_url_element.get_attribute('href')
        ssl = official_url.startswith('https') if official_url else False
    except Exception:
        official_url = ''
        ssl = False

    return {
        "店舗名": store_name,
        "電話番号": phone_number,
        "メールアドレス": email,
        "都道府県": prefecture,
        "市区町村": city,
        "番地": street,
        "建物名": building,
        "URL": official_url,
        "SSL": ssl
    }

# ページ遷移してデータを取得
while len(data) < 50:  # 最大50件まで取得
    print("現在のページを処理中...")
    time.sleep(3)  # サーバー負荷軽減のため待機

    # 店舗リンクの取得
    store_links = driver.find_elements(By.CSS_SELECTOR, 'a.style_titleLink__oiHVJ')
    links = [link.get_attribute('href') for link in store_links]

    # 各店舗の詳細ページを処理
    for link in links:
        print(f"処理中: {link}")
        retries = 3
        while retries > 0:
            try:
                details = extract_details(link)
                data.append(details)
                if len(data) >= 50:
                    break
                retries = 0
            except Exception as e:
                retries -= 1
                print(f"エラーが発生しました: {e}. リトライします...({3-retries}/3)")
                if retries == 0:
                    print(f"失敗: {link}")
                    traceback.print_exc()

    try:
        # 次へボタンの取得とクリック
        next_button = driver.find_element(By.CSS_SELECTOR, 'img.style_nextIcon__M_Me')
        next_button.click()
        print("次のページに移動しました。")
    except Exception as e:
        print(f"次のページへの移動に失敗しました: {e}")
        break

# ブラウザを終了
driver.quit()

# データフレームに変換
df = pd.DataFrame(data)

# CSVとして保存
df.to_csv('1-2.csv', index=False, encoding='utf-8-sig')
print("データが 1-2.csv に保存されました。")

# データ確認
print(df.head())