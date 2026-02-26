import unittest
from src.crawler.spider import Spider
from src.crawler.parser import Parser

class TestCrawler(unittest.TestCase):

    def setUp(self):
        self.spider = Spider()
        self.parser = Parser()

    def test_start_crawl(self):
        result = self.spider.start_crawl('http://example.com')
        self.assertTrue(result)

    def test_parse_page(self):
        html_content = "<html><body><h1>Test</h1></body></html>"
        data = self.parser.extract_data(html_content)
        self.assertIn('Test', data)

if __name__ == '__main__':
    unittest.main()