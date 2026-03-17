from app.models import Team, Match, Event
from .blue_alliance_client import BlueAllianceClient


class BlueAllianceSync:
    def __init__(self):
        self.client = BlueAllianceClient()

    def sync_district_events(self, district_key)