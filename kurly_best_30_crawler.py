import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import re

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kurly_best_30_crawling.log'),
        logging.StreamHandler()
    ]
)

class KurlyBest30Crawler:
    def __init__(self, output_dir: str = "kurly_best_30_data"):
        """컬리 베스트 탭 상위 30개 제품 크롤링"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        
        self.base_review_params = {
            "sortType": "RECOMMEND",
            "size": 10,
            "onlyImage": "false",
            "filters": "",
        }
        
        # 컬리 베스트 제품 수 (상위 30개만 필요)
        self.limit_count = 30
    
    def get_best_products(self) -> List[Dict]:
        """베스트 탭에서 상위 30개 제품 기본 정보 수집"""
        url = "https://www.kurly.com/collection-groups/beauty-best?site=beauty&page=1&collection=beauty-bestproduct"
        all_products = []
        
        try:
            logging.info(f"베스트 탭 페이지 요청 중: {url}")
            
            res = requests.get(url, headers=self.headers, timeout=10)
            res.raise_for_status()
            
            # HTML 파싱
            soup = BeautifulSoup(res.content, 'html.parser')
            
            # 디버깅: HTML 저장 (구조 확인 용)
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            logging.info("디버깅: HTML을 debug_page.html로 저장했습니다.")
            
            # 다양한 선택자 시도
            selectors = [
                soup.find_all('div', {'class': re.compile(r'product|Product')}),
                soup.find_all('article', {'class': re.compile(r'product|Product')}),
                soup.find_all('li', {'class': re.compile(r'product|Product')}),
                soup.find_all('a', {'class': re.compile(r'product-item|productCard')}),
            ]
            
            product_elements = []
            for selector_result in selectors:
                if selector_result:
                    product_elements = selector_result
                    logging.info(f"선택자 일치: {len(product_elements)}개 요소 발견")
                    break
            
            # 모두 없으면 전체 HTML에서 "product"라는 텍스트 함유 요소 찾기
            if not product_elements:
                logging.warning("기본 선택자로 제품을 찾지 못했습니다. 모든 div 검색 중...")
                product_elements = soup.find_all('div', limit=100)
            
            logging.info(f"HTML에서 {len(product_elements)}개의 제품 요소 검색 중")
            
            # 제품 정보 추출
            for idx, elem in enumerate(product_elements[:self.limit_count], 1):
                try:
                    # 제품 번호 추출 (data-product-no 또는 href에서)
                    link = elem.find('a', href=True)
                    if not link:
                        continue
                    
                    href = link.get('href', '')
                    # URL에서 제품 번호 추출
                    match = re.search(r'/products/(\d+)', href)
                    product_no = match.group(1) if match else None
                    
                    if not product_no:
                        continue
                    
                    # 제품명
                    name_elem = elem.find('div', {'class': re.compile(r'name|title')})
                    name = name_elem.get_text(strip=True) if name_elem else "Unknown"
                    
                    # 가격
                    price_elem = elem.find('span', {'class': re.compile(r'price|amount')})
                    price = price_elem.get_text(strip=True) if price_elem else "0"
                    
                    # 이미지 URL
                    img_elem = elem.find('img')
                    img_url = img_elem.get('src', '') if img_elem else ""
                    
                    product_info = {
                        "rank": idx,
                        "no": int(product_no),
                        "name": name,
                        "href": href,
                        "sales_price": price,
                        "product_vertical_medium_url": img_url,
                    }
                    all_products.append(product_info)
                    
                except Exception as e:
                    logging.warning(f"제품 정보 추출 실패 (rank {idx}): {e}")
                    continue
            
            logging.info(f"총 {len(all_products)}개 제품 정보 수집 완료")
            return all_products
            
        except Exception as e:
            logging.error(f"베스트 탭 페이지 크롤링 실패: {e}")
            return []
    
    def get_product_notice_and_review_count(self, product_no: int) -> Optional[Dict]:
        """제품 공지사항 정보 및 리뷰 카운트 수집"""
        url = f"https://api.kurly.com/showroom/v2/products/{product_no}?join_order_code="
        
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            res.raise_for_status()
            data = res.json().get("data", {})
            
            # product_notice에서 notices 추출
            product_notice = data.get("product_notice", [])
            notices = []
            if product_notice and len(product_notice) > 0:
                notices = product_notice[0].get("notices", [])
            
            return {
                "no": data.get("no"),
                "product_notice_notices": notices,
                "review_count": data.get("review_count", 0)
            }
            
        except Exception as e:
            logging.error(f"제품 공지 수집 실패 (product_no: {product_no}): {e}")
            return None
    
    def get_top_reviews(self, product_no: int, limit: int = 5) -> List[Dict]:
        """제품의 상위 리뷰만 수집 (최대 5개)"""
        url = f"https://api.kurly.com/product-review/v3/contents-products/{product_no}/reviews"
        reviews = []
        
        try:
            params = dict(self.base_review_params)
            params["size"] = limit  # 5개만 요청
            
            res = requests.get(url, headers=self.headers, params=params, timeout=10)
            res.raise_for_status()
            
            data = res.json()
            review_data = data.get("data", [])
            
            # 필요한 필드만 추출
            for review in review_data[:limit]:
                reviews.append({
                    "contents": review.get("contents"),
                    "registeredAt": review.get("registeredAt")
                })
            
            return reviews
            
        except Exception as e:
            logging.error(f"리뷰 수집 실패 (product_no: {product_no}): {e}")
            return []
    
    def crawl_product(self, product_info: Dict) -> Optional[Dict]:
        """단일 제품의 추가 데이터 수집 및 병합"""
        product_no = product_info.get("no")
        rank = product_info.get("rank")
        
        logging.info(f"[{rank}/30] Product {product_no}: {product_info.get('name')} 크롤링 중...")
        
        try:
            # 1. 제품 공지 및 리뷰 카운트 정보
            product_notice = self.get_product_notice_and_review_count(product_no)
            if not product_notice:
                return None
            
            time.sleep(0.3)
            
            # 2. 상위 리뷰 정보 (최대 5개)
            reviews = self.get_top_reviews(product_no, limit=5)
            
            # 3. 데이터 병합
            merged_data = {
                "rank": rank,
                "product_no": product_no,
                "name": product_info.get("name"),
                "review_count": product_notice.get("review_count", 0),
                "short_description": product_info.get("short_description"),
                "product_vertical_medium_url": product_info.get("product_vertical_medium_url"),
                "sales_price": product_info.get("sales_price"),
                "discounted_price": product_info.get("discounted_price"),
                "product_notice_notices": product_notice.get("product_notice_notices", []),
                "top_reviews": reviews
            }
            
            logging.info(f"[{rank}/30] Product {product_no}: 완료 (리뷰 {len(reviews)}개)")
            return merged_data
            
        except Exception as e:
            logging.error(f"[{rank}/30] Product {product_no}: 크롤링 실패 - {e}")
            return None
    
    def crawl_best_30(self):
        """베스트 탭 상위 30개 제품 크롤링 및 저장"""
        logging.info("=" * 60)
        logging.info("컬리 베스트 탭 상위 30개 제품 크롤링 시작")
        logging.info("=" * 60)
        
        start_time = time.time()
        
        # 1. 베스트 탭에서 상위 30개 제품 기본 정보 수집
        products_info = self.get_best_products()
        
        if not products_info:
            logging.error("제품 정보를 가져올 수 없습니다.")
            return
        
        # 2. 각 제품의 추가 정보 크롤링
        all_products = []
        
        for product_info in products_info:
            product_data = self.crawl_product(product_info)
            
            if product_data:
                all_products.append(product_data)
            
            # 제품 간 딜레이
            time.sleep(1)
        
        # 3. 결과 저장
        output_file = self.output_dir / "kurly_best_30_products.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)
        
        elapsed_time = time.time() - start_time
        
        logging.info("=" * 60)
        logging.info("크롤링 완료")
        logging.info("=" * 60)
        logging.info(f"총 {len(all_products)}개 제품 데이터 저장")
        logging.info(f"소요 시간: {elapsed_time:.2f}초")
        logging.info(f"저장 위치: {output_file}")
        logging.info("=" * 60)


if __name__ == "__main__":
    crawler = KurlyBest30Crawler(output_dir="kurly_best_30_data")
    crawler.crawl_best_30()
