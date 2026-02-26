import sys
import os

# src 폴더를 경로에 강제 추가하여 모듈 인식 문제 해결
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from crawler.spider import Spider

def main():
    # URL을 명시적으로 전달하여 명확하게 실행
    target_url = "https://www.kurly.com/categories/167001?site=beauty"
    crawler = Spider(start_url=target_url)
    crawler.start_crawl()

if __name__ == "__main__":
    main()