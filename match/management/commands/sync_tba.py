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

    def handle(self, *args, **options):
        sync = BlueAllianceSync()

        district_key = options['district']

        if district_key:
            self.stdout.write(f"Syncing data for {district_key}...")

            sync.sync_district_events(district_key)

            
            # Call your sync function here
            self.stdout.write(self.style.SUCCESS(f'Successfully synced {district_key}'))
        else:
            self.stdout.write(self.style.WARNING("No event key provided. Syncing all WI events..."))
            # Logic for bulk sync