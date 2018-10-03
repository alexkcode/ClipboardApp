from scrapy.spiders import Spider

from data_utils import DataUtils
from spider_base import SpiderBase

class ForMyBlockSpider(Spider, SpiderBase):
    name = 'my hood my block my city'
    allowed_domains = ['www.formyblock.org']

    def __init__(self, start_date, end_date):
        SpiderBase.__init__(self, 
                            self.allowed_domains[0], 
                            start_date, 
        	                end_date, 
                            date_format = '%W, %M %e, %Y')

    def start_requests(self):
        yield self.get_request('events/', {})

    def parse(self, response):
        