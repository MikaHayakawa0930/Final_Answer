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

def scrape_store_links(html):
    #ページ内の店舗リンクを取得する関数
    soup = BeautifulSoup(html, 'html.parser')
    store_links = [
        BASE_URL + link['href'] if link['href'].startswith('/') else link['href']
        for link in soup.select('a.style_titleLink__oiHVJ')
    ]
    return store_links

def get_next_page_url(html):
    #次のページのURLを取得する関数
    soup = BeautifulSoup(html, 'html.parser')
    next_page_element = soup.select_one('a[href*="?p="]')
    if next_page_element:
        next_page_url = next_page_element['href']
        return BASE_URL + next_page_url if next_page_url.startswith('/') else next_page_url
    return None

def extract_details(detail_url):
    #店舗詳細ページから情報を抽出する関数
    html = fetch_html(detail_url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')

    try:
        store_name = soup.select_one('h1').text.strip() if soup.select_one('h1') else ''
    except:
        store_name = ''

    try:
        phone_number = soup.select_one('tr#info-phone span.number').text.strip() if soup.select_one('tr#info-phone span.number') else ''
    except:
        phone_number = ''

    # メールアドレスを正規表現で抽出
    try:
        email = ''
        email_candidates = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html)
        if email_candidates:
            email = email_candidates[0]  # 最初に見つかったメールアドレスを取得
    except:
        email = ''
    
    try:
        address_element = soup.select_one('p.adr')
        region = address_element.select_one('span.region').text.strip() if address_element and address_element.select_one('span.region') else ''
        locality = address_element.select_one('span.locality').text.strip() if address_element and address_element.select_one('span.locality') else ''
        address = f"{region} {locality}"

        address = re.sub(r'\d{3}-\d{4}', '', address).strip()
        pattern = re.compile(r'^(.*?[都道府県])(.*?[市区町村])(.*)$')
        match = pattern.match(address)
        if match:
            prefecture, city, rest_address = match.groups()
            street, building = rest_address.split(' ', 1) if ' ' in rest_address else (rest_address, '')
        else:
            prefecture, city, street, building = '', '', '', ''
    except:
        prefecture, city, street, building = '', '', '', ''

    official_url = ""
    ssl = ""

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

# メイン処理
page_url = f'{BASE_URL}/eki/0006423/rs/'
while len(data) < 50:  # 最大50件まで取得
    print("現在のページを処理中...")
    html = fetch_html(page_url)
    if not html:
        break

    try:
        links = scrape_store_links(html)

        for link in links:
            print(f"処理中: {link}")
            details = extract_details(link)
            if details:
                data.append(details)
            if len(data) >= 50:
                break
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print(traceback.format_exc())

    next_page_url = get_next_page_url(html)
    if next_page_url:
        page_url = next_page_url
        print(f"次のページに移動しました: {page_url}")
    else:
        print("次のページがありません。処理を終了します。")
        break

df = pd.DataFrame(data)
df.to_csv('1-1.csv', index=False, encoding='utf-8-sig')
print("データが 1-1.csv に保存されました。")