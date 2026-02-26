import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from crawler.spider import Spider

def main():
    crawler = Spider()
    crawler.start_crawl()

if __name__ == "__main__":
    main()