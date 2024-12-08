import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import traceback

# ユーザーエージェントの設定
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# データ格納リスト
data = []

# ベースURL
BASE_URL = 'https://r.gnavi.co.jp'

def fetch_html(url):
    #指定されたURLからHTMLを取得する関数
    try:
        response = requests.get(url, headers=HEADERS)
        response.encoding = response.apparent_encoding  # エンコーディングを自動判定して設定
        time.sleep(3)  # サーバー負荷軽減のため待機
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to fetch {url} (status code: {response.status_code})")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def extract_details(detail_url):
    #店舗詳細ページから情報を抽出する関数
    html = fetch_html(detail_url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')

    try:
        # 店舗名を取得
        store_name = soup.select_one('h1').text.strip() if soup.select_one('h1') else ''
    except:
        store_name = ''

    try:
        # 電話番号を取得
        phone_number = soup.select_one('tr#info-phone span.number').text.strip() if soup.select_one('tr#info-phone span.number') else ''
    except:
        phone_number = ''

    email = ''  # メールアドレスは通常存在しないため空欄にする

    try:
        # 住所を取得し分割
        address_element = soup.select_one('p.adr')
        region = address_element.select_one('span.region').text.strip() if address_element and address_element.select_one('span.region') else ''
        locality = address_element.select_one('span.locality').text.strip() if address_element and address_element.select_one('span.locality') else ''
        address = f"{region} {locality}"

        # 郵便番号を除去
        address = re.sub(r'\d{3}-\d{4}', '', address).strip()

        # 正規表現で住所を分割
        pattern = re.compile(r'^(.*?[都道府県])(.*?[市区町村])(.*)$')
        match = pattern.match(address)
        if match:
            prefecture, city, rest_address = match.groups()
            street, building = rest_address.split(' ', 1) if ' ' in rest_address else (rest_address, '')
        else:
            prefecture, city, street, building = '', '', '', ''
    except:
        prefecture, city, street, building = '', '', '', ''

    try:
        # URLとSSL確認
        official_url = soup.select_one('a[href^="http"]')['href'] if soup.select_one('a[href^="http"]') else ''
        ssl = official_url.startswith('https') if official_url else False
    except:
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

def scrape_store_links(html):
    #ページ内の店舗リンクを取得する関数
    soup = BeautifulSoup(html, 'html.parser')
    store_links = [
        BASE_URL + link['href'] if link['href'].startswith('/') else link['href']
        for link in soup.select('a.style_titleLink__oiHVJ')
    ]
    return store_links

# メイン処理
page_url = f'{BASE_URL}/eki/0006423/rs/'
while len(data) < 50:  # 最大50件まで取得
    print("現在のページを処理中...")
    html = fetch_html(page_url)
    if not html:
        break

    try:
        # 店舗リンクを取得
        links = scrape_store_links(html)

        # 各店舗の詳細ページを処理
        for link in links:
            print(f"処理中: {link}")
            try:
                details = extract_details(link)
                if details:
                    data.append(details)
                if len(data) >= 50:
                    break
            except Exception as e:
                print(f"エラーが発生しました: {e}")
                print(traceback.format_exc())
    except Exception as e:
        print(f"ページ処理中にエラーが発生しました: {e}")
        print(traceback.format_exc())

    # 次のページのURLを取得
    soup = BeautifulSoup(html, 'html.parser')
    next_page = soup.select_one('a[href*="?p="]')  # "?p=" を含むリンクを選択
    if next_page:
        # 相対URLの場合はBASE_URLを補完
        page_url = BASE_URL + next_page['href'] if next_page['href'].startswith('/') else next_page['href']
        print(f"次のページに移動しました: {page_url}")
    else:
        print("次のページがありません。処理を終了します。")
        break
    
    
# データフレームに変換
df = pd.DataFrame(data)

# CSVとして保存
df.to_csv('1-1.csv', index=False, encoding='utf-8-sig')  # UTF-8-SIGで保存
print("データが 1-1.csv に保存されました。")

# データ確認
print(df.head())