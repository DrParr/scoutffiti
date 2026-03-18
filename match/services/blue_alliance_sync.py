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

    def sync_matches(self, event_key):
        matches_json = self.client.get_event_matches(event_key)

        self.sync_matches_from_json(event_key, matches_json)

    def sync_matches_from_json(self, event_key, matches_json):
        event = Event.objects.get(key=event_key)
        count = 0

        for m in matches_json:
            # 1. Sync the Match object
            # We use the TBA key (e.g., '2026wiply_qm1') as the unique lookup
            match_obj, created = Match.objects.update_or_create(
                key=m['key'],
                defaults={
                    'event': event,
                    'match_number': m['match_number'],
                    'comp_level': m['comp_level'],
                    'score_red': m['alliances']['red'].get('score'),
                    'score_blue': m['alliances']['blue'].get('score'),
                    'predicted_time': m.get('predicted_time'),
                    'actual_time': m.get('actual_time'),
                }
            )

            # 2. Process Red Alliance Teams
            red_team_objs = []
            for t_key in m['alliances']['red']['team_keys']:
                # Strip 'frc' to get the integer for the team_number field
                t_number = int(t_key.replace('frc', ''))
                
                # Using update_or_create here prevents the UNIQUE constraint error 
                # on team_number by updating the existing record if it exists.
                team, _ = Team.objects.update_or_create(
                    team_number=t_number,
                    defaults={
                        'key': t_key,
                    }
                )
                red_team_objs.append(team)

            # 3. Process Blue Alliance Teams
            blue_team_objs = []
            for t_key in m['alliances']['blue']['team_keys']:
                t_number = int(t_key.replace('frc', ''))
                
                team, _ = Team.objects.update_or_create(
                    team_number=t_number,
                    defaults={
                        'key': t_key,
                    }
                )
                blue_team_objs.append(team)

            # 4. Update the ManyToMany relationships
            match_obj.red_teams.set(red_team_objs)
            match_obj.blue_teams.set(blue_team_objs)

            if created:
                count += 1
                
        return count