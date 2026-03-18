from django.core.management.base import BaseCommand
from match.models import Event, District

from match.services.blue_alliance_sync import BlueAllianceSync


class Command(BaseCommand):
    help = 'Syncs Wisconsin Regional data from The Blue Alliance'

    def add_arguments(self, parser):
        # This allows you to run: python manage.py sync_tba --event 2026wiply
        parser.add_argument(
            '--district', 
            type=str, 
            help='Specific TBA district key to sync'
        )

        parser.add_argument(
            '--event', 
            type=str, 
            help='Specific TBA event key to sync'
        )

    def handle(self, *args, **options):
        sync = BlueAllianceSync()
        district_key = options['district']
        event_key = options['event']

        if district_key:
            self.stdout.write(f"Syncing data for {district_key}...")

            sync.sync_district_events(district_key)

            self.stdout.write(self.style.SUCCESS(f'Successfully synced {district_key}'))
        
        elif event_key:
            self.stdout.write(f"Syncing data for {event_key}...")

            sync.sync_matches(event_key)

            self.stdout.write(self.style.SUCCESS(f'Successfully synced {event_key}'))           

        else:
            self.stdout.write(self.style.WARNING("No key provided. Exiting..."))
            # Logic for bulk sync