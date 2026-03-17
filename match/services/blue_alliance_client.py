import requests


class BlueAllianceClient:
    BASE_URL = "https://www.thebluealliance.com/api/v3"

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"X-TBA-Auth-Key": self.api_key,
        "Content-Type": "application/json"}

    def get(self, endpoint_url, timeout = 10):
        url = f"{self.BASE_URL}/{endpoint_url}"
        respnose = requests.get(url, headers = self.headers, timeout = timeout)

        response.raise_for_status()
        return response.json()

    def get_event_keys(self, district_key):
        return self.get(f"/district/{district_key}/events/keys")
        
    def get_district_teams(self, district_key):
        return self.get(f"/district/{district_key}/teams")
        
    def get_event_matches(self, event_key):
        return self.get(f"/event/{event_key}/matches/simple")
        
    