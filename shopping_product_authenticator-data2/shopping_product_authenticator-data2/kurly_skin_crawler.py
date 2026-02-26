import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kurly_full_crawling.log'),
        logging.StreamHandler()
    ]
)

class KurlySkinCrawler:
    def __init__(self, output_dir: str = "kurly_skin_data"):
        """컬리 스킨케어 제품 전체 크롤링"""
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
    
    def get_all_products_from_category(self) -> List[Dict]:
        """카테고리의 모든 제품 기본 정보 수집"""
        url = "https://api.kurly.com/collection/v2/home/sites/beauty/product-categories/167001/products"
        all_products = []
        page = 1
        
        while True:
            try:
                params = {
                    "sort_type": 4,
                    "page": page,
                    "per_page": 100,
                    "filters": ""
                }
                res = requests.get(url, headers=self.headers, params=params, timeout=10)
                res.raise_for_status()
                
                data = res.json()
                products = data.get("data", [])
                
                if not products:
                    break
                
                # 필요한 필드만 추출
                for p in products:
                    product_info = {
                        "no": p.get("no"),
                        "name": p.get("name"),
                        "short_description": p.get("short_description"),
                        "product_vertical_medium_url": p.get("product_vertical_medium_url"),
                        "sales_price": p.get("sales_price"),
                        "discounted_price": p.get("discounted_price")
                    }
                    all_products.append(product_info)
                
                logging.info(f"페이지 {page}: {len(products)}개 제품 발견 (누적: {len(all_products)}개)")
                
                page += 1
                time.sleep(0.5)
                
            except Exception as e:
                logging.error(f"제품 정보 수집 실패 (페이지 {page}): {e}")
                break
        
        logging.info(f"총 {len(all_products)}개 제품 정보 수집 완료")
        return all_products
    
    def get_product_notice_and_review_count(self, product_no: int) -> Optional[Dict]:
        """제품 공지사항 정보 수집 (필요한 필드만)"""
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
                "product_notice_notices": notices,  # notices 배열
                "review_count": data.get("review_count", 0)
            }
            
        except Exception as e:
            logging.error(f"제품 공지 수집 실패 (product_no: {product_no}): {e}")
            return None
    
    def get_all_reviews(self, product_no: int) -> List[Dict]:
        """제품의 모든 리뷰 수집 (필요한 필드만)"""
        url = f"https://api.kurly.com/product-review/v3/contents-products/{product_no}/reviews"
        all_reviews = []
        after = None
        
        while True:
            try:
                params = dict(self.base_review_params)
                if after:
                    params["after"] = after
                
                res = requests.get(url, headers=self.headers, params=params, timeout=10)
                res.raise_for_status()
                
                data = res.json()
                reviews = data.get("data", [])
                
                # 필요한 필드만 추출
                for review in reviews:
                    all_reviews.append({
                        "contents": review.get("contents"),
                        "registeredAt": review.get("registeredAt")
                    })
                
                # 다음 페이지 확인
                after = data.get("meta", {}).get("pagination", {}).get("after")
                if after is None:
                    break
                
                time.sleep(0.5)
                
            except Exception as e:
                logging.error(f"리뷰 수집 실패 (product_no: {product_no}, after: {after}): {e}")
                break
        
        logging.info(f"Product {product_no}: {len(all_reviews)}개 리뷰 수집")
        return all_reviews
    
    def crawl_product(self, product_info: Dict) -> Optional[Dict]:
        """단일 제품의 추가 데이터 수집 및 병합"""
        product_no = product_info.get("no")
        logging.info(f"=== Product {product_no} 크롤링 시작 ===")
        
        try:
            # 1. 제품 공지 및 리뷰 카운트 정보
            product_notice = self.get_product_notice_and_review_count(product_no)
            if not product_notice:
                return None
            
            time.sleep(0.3)
            
            # 2. 리뷰 정보
            reviews = self.get_all_reviews(product_no)
            
            # 3. 데이터 병합
            merged_data = {
                "product_no": product_no,
                "name": product_info.get("name"),
                "review_count": product_notice.get("review_count", 0),
                "short_description": product_info.get("short_description"),
                "product_vertical_medium_url": product_info.get("product_vertical_medium_url"),
                "sales_price": product_info.get("sales_price"),
                "discounted_price": product_info.get("discounted_price"),
                "product_notice_notices": product_notice.get("product_notice_notices", []),
                "reviews": reviews
            }
            
            logging.info(f"Product {product_no}: 크롤링 완료 (리뷰 {len(reviews)}개)")
            return merged_data
            
        except Exception as e:
            logging.error(f"Product {product_no}: 크롤링 실패 - {e}")
            return None
    
    def crawl_all(self):
        """모든 제품 크롤링 및 저장"""
        # 1. 카테고리에서 모든 제품 기본 정보 수집
        products_info = self.get_all_products_from_category()
        
        if not products_info:
            logging.error("제품 정보를 가져올 수 없습니다.")
            return
        
        # 2. 각 제품의 추가 정보 크롤링
        all_products = []
        
        for idx, product_info in enumerate(products_info):
            logging.info(f"\n진행률: {idx+1}/{len(products_info)} ({(idx+1)/len(products_info)*100:.1f}%)")
            
            product_data = self.crawl_product(product_info)
            
            if product_data:
                all_products.append(product_data)
            
            # 제품 간 딜레이
            time.sleep(1)
        
        # 3. 결과 저장
        output_file = self.output_dir / "kurly_skin_products_merged.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)
        
        logging.info(f"\n=== 크롤링 완료 ===")
        logging.info(f"총 {len(all_products)}개 제품 데이터 저장")
        logging.info(f"저장 위치: {output_file}")


if __name__ == "__main__":
    crawler = KurlySkinCrawler(output_dir="kurly_skin_data")
    crawler.crawl_all()