import time
import pandas as pd
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class Spider:
    def __init__(self):
        self.base_url = "https://www.kurly.com/categories/167001?site=beauty"
        self.products = []
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # 백그라운드 실행 (선택)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def start_crawl(self):
        """메인 크롤링 시작"""
        try:
            print("크롤링 시작...")
            self.driver.get(self.base_url)
            time.sleep(3)  # 페이지 로드 대기
            
            self.crawl_products()
            self.save_data()
            print(f"총 {len(self.products)}개 상품 수집 완료")
        finally:
            self.driver.quit()
    
    def crawl_products(self):
        """상품 정보 크롤링"""
        scroll_count = 0
        last_count = 0
        
        while len(self.products) < 100:
            # 페이지 아래로 스크롤
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print(f"스크롤 {scroll_count + 1}회 수행 중...")
            time.sleep(2)  # 콘텐츠 로드 대기
            
            # 상품 요소 추출
            products = self.driver.find_elements(By.CSS_SELECTOR, "div.product_card")
            
            print(f"현재 감지된 상품 수: {len(products)}")
            
            for product in products[last_count:]:
                if len(self.products) >= 100:
                    break
                
                try:
                    # 상품명
                    name_elem = product.find_element(By.CSS_SELECTOR, "span.product_name")
                    name = name_elem.text.strip()
                    
                    # 가격
                    price_elem = product.find_element(By.CSS_SELECTOR, "span.product_price")
                    price = price_elem.text.strip()
                    
                    # 이미지 URL
                    img_elem = product.find_element(By.CSS_SELECTOR, "img")
                    image_url = img_elem.get_attribute("src")
                    
                    # URL
                    link_elem = product.find_element(By.CSS_SELECTOR, "a")
                    url = link_elem.get_attribute("href")
                    
                    product_data = {
                        'name': name,
                        'price': price,
                        'image_url': image_url,
                        'url': url
                    }
                    
                    self.products.append(product_data)
                    print(f"[{len(self.products)}] {name} - {price}")
                    
                except Exception as e:
                    print(f"상품 파싱 오류: {e}")
                    continue
            
            last_count = len(products)
            scroll_count += 1
            
            # 100개 수집 완료 시 종료
            if len(self.products) >= 100:
                break
            
            # 최대 스크롤 횟수 제한 (무한 루프 방지)
            if scroll_count > 15:
                print("최대 스크롤 횟수 도달")
                break
            
            time.sleep(1)  # 서버 부하 방지
    
    def save_data(self):
        """데이터 저장"""
        raw_dir = Path('data/raw')
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame(self.products)
        csv_path = raw_dir / 'kurly_skincare.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"데이터 저장 완료: {csv_path}")