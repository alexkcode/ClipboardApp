import time
from scrapy import Item
from scrapy.loader import ItemLoader
from models.category import Category
from util.data_utils import DataUtils
from base.custom_spiders import ApiSpider
import scrapy

class LibraryEvents(ApiSpider):
    # This is the max amount of rows that the API can return at one time
    MAX_ROWS = 50

    name = 'library'
    
    def __init__(self, name=None, **kwargs):
        super().__init__(self, 'Chicago Public Library', 'https://chipublib.bibliocommons.com/', date_format = '%Y-%m-%d', **kwargs)
    
    def parse(self, response):
        return self.get_events()

    def get_next_events_json(self, start):
        request_params = {
            'client_scope': 'events', 
            'query': f'start={start}&rows={self.MAX_ROWS}',
            'facet_fields': 'branch_location_id', 
            'local_start': f'{self.start_date} TO {self.end_date}',
            'include_near_location': 'false'
        }
        return self.get_response_json(endpoint='events/events/search', request_params=request_params, property_to_return = 'events')

    def get_events_json(self):
        start = 0
        events_json = []
        more_data = True

        while more_data:
            # Sleep to avoid overloading the server
            self.wait()
            next_events_json = self.get_next_events_json(start)
            num_results = len(next_events_json)
            events_json.extend(next_events_json)
            # Keep querying until no more data is returned
            more_data = num_results > 0
            start += num_results
        
        return events_json

    def get_locations_json(self, location_category):
        # location_category = 'locations' for branch locations and 'places' for non-branch locations
        request_params = {
            'client_scope': 'events', 
            'limit': '0'
        }
        return self.get_response_json(endpoint='events/' + location_category, request_params=request_params, property_to_return = location_category)
    
    def get_branch_locations_json(self):
        return self.get_locations_json('locations')

    def get_nonbranch_locations_json(self):
        return self.get_locations_json('places')
    
    def get_locations_list(self, get_locations_func):
        return { location['id']: location['address'] for location in get_locations_func() }

    def get_branch_locations_list(self):
        return self.get_locations_list(self.get_branch_locations_json)

    def get_nonbranch_locations_list(self):
        return self.get_locations_list(self.get_nonbranch_locations_json)

    def get_address_string(self, location):
        # Any data that isn't included will be set to 'None', so just replace it with an empty string
        return f"{location['number']} {location['street']} {location['city']}, {location['state']} {location['zip']}".replace('None', '')

    def get_events(self):
        events_json = self.get_events_json()
        branch_locations = self.get_branch_locations_list()
        nonbranch_locations = self.get_nonbranch_locations_list()

        for event in events_json:
            details = event['definition']
            branch_location_id = details['branch_location_id']
            # Determine if branch or non-branch event
            if branch_location_id == None:
                non_branch_location_id = details['non_branch_location_id']
                location = nonbranch_locations[non_branch_location_id]
            else:
                location = branch_locations[branch_location_id]

            try:
                date, start_time = details['start'].split('T')
                end_time = details['end'].split('T')[1]
            except ValueError:
                # Assume event is all day if no time is supplied
                date = details['start']
                start_time = end_time = 'All Day'

            # Don't show cancelled or full events
            if details['is_cancelled'] == True or event['is_full'] == True:
                continue
            
            yield {
                'title': details['title'],
                'description': details['description'],
                'address': self.get_address_string(location),
                'event_time': {
                    'date': date,
                    'start_time': start_time,
                    'end_time': end_time
                },
                'url': f'{self.base_url}events/search/index/event/{event["id"]}',
                'price': 0.0,
                'category': Category.LIBRARY
            }