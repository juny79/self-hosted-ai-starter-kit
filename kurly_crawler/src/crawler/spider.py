import pandas as pd
import json
import time
import random
import sys
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# --- 1. 경로 및 파일 설정 ---
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
csv_path = project_root / 'data' / 'raw' / 'kurly_skincare.csv'
save_path = project_root / 'kurly_products_result.json'

print(f"읽을 파일: {csv_path}")

try:
    df = pd.read_csv(csv_path)
    if 'url' in df.columns:
        product_urls = df['url'].tolist()
    elif 'no' in df.columns:
        product_urls = [f"https://www.kurly.com/goods/{no}" for no in df['no']]
    else:
        print("CSV에 url 또는 no 컬럼이 없습니다.")
        sys.exit(1)
except Exception as e:
    print(f"CSV 파일 로드 중 에러: {e}")
    sys.exit(1)

# --- 2. 브라우저 설정 ---
options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
options.add_argument("--disable-blink-features=AutomationControlled")
# options.add_argument("--headless") # 디버깅을 위해 창을 띄움
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

crawled_data = []

print(f"총 {len(product_urls)}개 상품 크롤링 시작...")

try:
    for idx, url in enumerate(product_urls):
        try:
            print(f"[{idx+1}/{len(product_urls)}] 접속: {url}")
            driver.get(url)
            
            # 페이지 로딩 대기
            time.sleep(random.uniform(2, 3))
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # --- [핵심] JSON 데이터 추출 시도 (__NEXT_DATA__) ---
            # 마켓컬리는 Next.js를 사용하므로 페이지 소스 안에 모든 데이터가 JSON으로 들어있을 확률이 높습니다.
            json_data = None
            next_data_script = soup.find("script", {"id": "__NEXT_DATA__"})
            
            name = ""
            sale_price = ""
            original_price = ""
            discount_rate = ""
            description = ""
            detail_info_text = ""
            reviews = []

            # 1. JSON 데이터로 정보 추출 (가장 정확함)
            if next_data_script:
                try:
                    data = json.loads(next_data_script.string)
                    # 구조: props -> pageProps -> goods -> name, price 등
                    goods = data.get('props', {}).get('pageProps', {}).get('goods', {})
                    
                    if goods:
                        name = goods.get('name', '')
                        description = goods.get('short_description', '')
                        sale_price = str(goods.get('price', ''))
                        original_price = str(goods.get('original_price', ''))
                        discount_rate = str(goods.get('discount_rate', '0')) + "%"
                        
                        # 상세정보 HTML 텍스트 변환
                        details_html = goods.get('description', '')
                        if details_html:
                            detail_bs = BeautifulSoup(details_html, 'html.parser')
                            detail_info_text = detail_bs.get_text('\n', strip=True) 
                            # 이미지 alt 텍스트도 추가
                            for img in detail_bs.find_all('img'):
                                if img.get('alt'):
                                    detail_info_text += f"\n[이미지: {img.get('alt')}]"
                        
                        print("   -> [성공] JSON 데이터 추출 완료")
                except Exception as e:
                    print(f"   -> JSON 파싱 실패, HTML 파싱으로 전환: {e}")

            # 2. HTML 직접 파싱 (JSON 실패 시 백업)
            if not name:
                try: name = soup.select_one('h1').text.strip()
                except: pass
            
            if not sale_price:
                 # 가격 정보 (여러 패턴 시도)
                try:
                    price_elem = soup.find('span', string=re.compile(r'[\d,]+원'))
                    if price_elem: sale_price = price_elem.text.strip()
                except: pass

            # 3. 후기 수집 (JSON에는 리뷰 리스트가 보통 없으므로 Selenium 클릭 필수)
            try:
                # '후기' 탭 클릭 시도
                review_btn = driver.find_elements(By.XPATH, "//span[contains(text(), '후기')] | //button[contains(., '후기')]")
                
                if review_btn:
                    # 클릭 가능한 요소 찾아서 클릭
                    driver.execute_script("arguments[0].click();", review_btn[0])
                    time.sleep(2) # 로딩 대기
                    
                    # 다시 파싱
                    review_soup = BeautifulSoup(driver.page_source, 'html.parser')
                    
                    # 리뷰 컨테이너 찾기 (다양한 클래스 대응)
                    # 보통 article 태그나 특정 div를 사용함
                    review_articles = review_soup.find_all('article')
                    if not review_articles:
                        review_articles = review_soup.select('div[class*="review"]')

                    for rv in review_articles[:10]: # 최대 10개
                        # 내용이 있는 텍스트만 추출
                        text = rv.get_text(" ", strip=True)
                        # 너무 짧거나 시스템 문구 제외
                        if len(text) > 10 and "도움이 돼요" not in text:
                            reviews.append(text[:300]) # 길이 제한
            except Exception as e:
                print(f"   -> 후기 수집 중 오류: {e}")

            # 데이터 저장 구조
            product_data = {
                "product_no": url.split('/')[-1],
                "url": url,
                "name": name,
                "sale_price": sale_price,
                "original_price": original_price,
                "discount_rate": discount_rate,
                "description": description,
                "detail_info_text": detail_info_text[:1000], # 너무 길면 자름
                "reviews": list(set(reviews)) # 중복 제거
            }
            
            crawled_data.append(product_data)
            print(f"   -> 수집됨: {name} ({sale_price}) | 후기 {len(reviews)}건")

            # 10개마다 중간 저장
            if (idx + 1) % 10 == 0:
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(crawled_data, f, ensure_ascii=False, indent=4)

        except Exception as e:
            print(f"   -> 치명적 오류 ({idx}): {e}")

except KeyboardInterrupt:
    print("사용자 중단")

finally:
    driver.quit()
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(crawled_data, f, ensure_ascii=False, indent=4)
    print(f"완료. 저장 파일: {save_path}")