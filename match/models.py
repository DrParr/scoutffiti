from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, Case, When, Value, IntegerField

# --- CUSTOM MANAGER FOR TOURNAMENT ORDERING ---

class MatchManager(models.Manager):
    def get_queryset(self):
        """
        Orders matches by tournament logic: Quals (1), Semis (2), Finals (3).
        Annotates a 'level_weight' for sorting purposes.
        """
        return super().get_queryset().annotate(
            level_weight=Case(
                When(comp_level__iexact='qm', then=Value(1)),
                When(comp_level__iexact='sf', then=Value(2)),
                When(comp_level__iexact='f', then=Value(3)),
                default=Value(4),
                output_field=IntegerField(),
            )
        ).order_by('level_weight', 'match_number', 'key')

# --- MODELS ---

class Team(models.Model):
    key = models.CharField(max_length=20, primary_key=True)
    team_number = models.IntegerField(unique=True)
    nickname = models.CharField(max_length=100, blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    
    city = models.CharField(max_length=100, blank=True, null=True)
    state_prov = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    
    school_name = models.CharField(max_length=255, blank=True, null=True)
    rookie_year = models.IntegerField(null=True, blank=True)
    website = models.URLField(max_length=255, blank=True, null=True)
    motto = models.TextField(blank=True, null=True)

    gmaps_url = models.URLField(max_length=500, blank=True, null=True)
    gmaps_place_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['team_number']

    def __str__(self):
        return f"{self.team_number} | {self.nickname}"

class District(models.Model):
    key = models.CharField(max_length=20, primary_key=True)
    abbreviation = models.CharField(max_length=10)
    display_name = models.CharField(max_length=100)

    def __str__(self):
        return self.display_name

class Event(models.Model):
    key = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=100, null=True, blank=True)
    year = models.IntegerField()
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    week = models.IntegerField(null=True, blank=True)

    location_name = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state_prov = models.CharField(max_length=50, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    
    event_type_string = models.CharField(max_length=100, null=True, blank=True)
    website = models.URLField(max_length=500, null=True, blank=True)
    
    district = models.ForeignKey(
        District, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='events'
    )

    def __str__(self):
        return self.short_name or self.name

class Match(models.Model):
    # 'key' is the Primary Key, so 'id' does not exist in this model
    key = models.CharField(max_length=20, primary_key=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='matches')
    
    match_number = models.IntegerField()
    comp_level = models.CharField(max_length=10) # qm, sf, f
    
    # Used for chronological ordering if match_numbers repeat
    sequence = models.IntegerField(default=0)

    red_teams = models.ManyToManyField(Team, related_name='red_matches')
    blue_teams = models.ManyToManyField(Team, related_name='blue_matches')

    score_red = models.IntegerField(null=True, blank=True)
    score_blue = models.IntegerField(null=True, blank=True)
    
    predicted_time = models.IntegerField(null=True, blank=True)
    actual_time = models.IntegerField(null=True, blank=True)

    # Attach the custom manager for tournament logic
    objects = MatchManager()

    class Meta:
        ordering = ['sequence', 'match_number']

    @property
    def verbose_name(self):
        mapping = {'qm': 'Quals', 'sf': 'Semis', 'f': 'Finals'}
        prefix = mapping.get(self.comp_level.lower(), self.comp_level.upper())
        return f"{prefix} {self.match_number}"

    def __str__(self):
        return f"{self.event.short_name or self.event.name} - {self.verbose_name}"

    def get_teams_for_alliance(self, color):
        return self.red_teams.all() if color == 'red' else self.blue_teams.all()

    @property
    def is_played(self):
        return self.actual_time is not None

class MatchScoutReport(models.Model):
    ALLIANCE_CHOICES = [('red', 'Red'), ('blue', 'Blue')]
    
    scout = models.ForeignKey(User, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='scout_reports')
    alliance_color = models.CharField(max_length=4, choices=ALLIANCE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_alliance_score(self):
        total = self.period_data.aggregate(total=Sum('score_value'))['total']
        return total or 0

    @property
    def alliance_defense_index(self):
        return self.period_data.filter(defended=True).count()

    def __str__(self):
        return f"{self.match.verbose_name} - {self.alliance_color.upper()} ({self.scout.username})"

class TeamPeriodData(models.Model):
    PHASE_CHOICES = [
        ('auto', 'Autonomous'),
        ('p1', 'Tele-op 1'), ('p2', 'Tele-op 2'), ('p3', 'Tele-op 3'),
        ('p4', 'Tele-op 4'), ('p5', 'Tele-op 5'), ('p6', 'Tele-op 6'),
    ]

    report = models.ForeignKey(MatchScoutReport, related_name='period_data', on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    
    phase = models.CharField(max_length=10, choices=PHASE_CHOICES)
    score_value = models.IntegerField(default=0)
    
    defended = models.BooleanField(default=False)
    passed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('report', 'team', 'phase')

    def __str__(self):
        return f"{self.team.team_number} - {self.phase}"