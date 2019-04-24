from custom_spiders import ScraperSpider

from data_utils import DataUtils

class ForMyBlockSpider(ScraperSpider):
    name = 'formyblock'
    allowed_domains = ['formyblock.org']

    def start_requests(self):
        yield self.get_request('events/', {})

    def parse(self, response):
        return {
            'title': response.css('.eventlist-title-link::text'),
            'url': response.css('.eventlist-title-link::attr(href)'),
            'event_time': self.extract_multiple(
                {'date': "",
                'time_range': ""}, 
                response.css('.eventlist-meta-item eventlist-meta-date event-meta-item').extract()),
            'address': response.css('eventlist-meta-address-maplink')
        }