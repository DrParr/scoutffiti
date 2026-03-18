from django.db import models

class Team(models.Model):
    # e.g., "frc10264"
    key = models.CharField(max_length=20, primary_key=True)
    team_number = models.IntegerField(unique=True)
    nickname = models.CharField(max_length=100, blank=True, null=True)
    name = models.TextField(blank=True, null=True)  # Full formal name with sponsors
    
    # Location data
    city = models.CharField(max_length=100, blank=True, null=True)
    state_prov = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    
    # Organization/History
    school_name = models.CharField(max_length=255, blank=True, null=True)
    rookie_year = models.IntegerField(null=True, blank=True)
    website = models.URLField(max_length=255, blank=True, null=True)
    motto = models.TextField(blank=True, null=True)

    # Social/Map links
    gmaps_url = models.URLField(max_length=500, blank=True, null=True)
    gmaps_place_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['team_number']

    def __str__(self):
        return f"{self.team_number} | {self.nickname}"

class District(models.Model):
    # e.g., '2026fit', '2026fma', '2026wi'
    key = models.CharField(max_length=20, primary_key=True)
    abbreviation = models.CharField(max_length=10) # e.g., 'WI'
    display_name = models.CharField(max_length=100) # e.g., 'FIRST Wisconsin'

    def __str__(self):
        return self.display_name

class Event(models.Model):
    key = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=100, null=True, blank=True)
    year = models.IntegerField()
    
    # Dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    week = models.IntegerField(null=True, blank=True) # FRC Week (0-6)

    # Location Info
    location_name = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state_prov = models.CharField(max_length=50, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    
    # Classification
    event_type_string = models.CharField(max_length=100, null=True, blank=True)
    website = models.URLField(max_length=500, null=True, blank=True)
    
    district = models.ForeignKey(
        'District', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='events'
    )

    def __str__(self):
        return self.short_name or self.name

class Match(models.Model):
    key = models.CharField(max_length=20, primary_key=True)
    # Link to the Event table
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='matches')
    
    match_number = models.IntegerField()
    comp_level = models.CharField(max_length=10)
    
    red_teams = models.ManyToManyField(Team, related_name='red_matches')
    blue_teams = models.ManyToManyField(Team, related_name='blue_matches')

    # Scoring (Keep these null until the match is played)
    score_red = models.IntegerField(null=True, blank=True)
    score_blue = models.IntegerField(null=True, blank=True)
    
    # Timing (Unix Timestamps)
    predicted_time = models.IntegerField(null=True, blank=True)
    actual_time = models.IntegerField(null=True, blank=True)

    class Meta:
        # This keeps your schedule in the correct order automatically
        ordering = ['match_number']

    def __str__(self):
        return f"{self.comp_level.upper()} {self.match_number}"

    @property
    def is_played(self):
        """Quick check to see if the match is over."""
        return self.actual_time is not None