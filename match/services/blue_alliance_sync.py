from match.models import Team, Match, Event, District
from django.conf import settings

from .blue_alliance_client import BlueAllianceClient


class BlueAllianceSync:
    def __init__(self):
        self.api_key = settings.TBA_API_KEY

        self.client = BlueAllianceClient(self.api_key)

    def sync_district_events(self, district_key):
        event_data = self.client.get_district_events(district_key)

        self.sync_events_from_json(event_data)

    def sync_events_from_json(self, events_json):
        count = 0
        for event_data in events_json:
            # Handle District as before...
            district_obj = None
            if event_data.get('district'):
                district_obj, _ = District.objects.update_or_create(
                    key=event_data['district']['key'],
                    defaults={
                        'abbreviation': event_data['district']['abbreviation'],
                        'display_name': event_data['district']['display_name'],
                    }
                )

            # Sync all "Important Pieces"
            event_obj, created = Event.objects.update_or_create(
                key=event_data['key'],
                defaults={
                    'name': event_data.get('name'),
                    'short_name': event_data.get('short_name'),
                    'year': event_data.get('year'),
                    'start_date': event_data.get('start_date'),
                    'end_date': event_data.get('end_date'),
                    'week': event_data.get('week'),
                    'location_name': event_data.get('location_name'),
                    'city': event_data.get('city'),
                    'state_prov': event_data.get('state_prov'),
                    'postal_code': event_data.get('postal_code'),
                    'event_type_string': event_data.get('event_type_string'),
                    'website': event_data.get('website'),
                    'district': district_obj,
                }
            )
            if created: count += 1
        return count