from django.contrib import admin
from .models import Team, Match, Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('year', 'event_code', 'name', 'start_date')
    list_filter = ('year',)
    # This search_field is CRITICAL for the Match autocomplete to work
    search_fields = ('name', 'key', 'event_code')
    ordering = ('-year', 'event_code')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('team_number', 'nickname', 'city', 'state_prov')
    search_fields = ('team_number', 'nickname', 'city')
    # search_fields must be defined for teams to show up in the match autocomplete/selector
    ordering = ('team_number',)

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    # Now we display the Event name instead of just a raw key string
    list_display = ('event', 'comp_level', 'match_number', 'score_red', 'score_blue', 'is_played')
    
    # You can now filter by Year or Event name in the sidebar!
    list_filter = ('event__year', 'event__name', 'comp_level')
    
    # 1. Use autocomplete_fields for the Event ForeignKey
    # This replaces a massive dropdown with a searchable text box
    autocomplete_fields = ['event']

    # 2. Use filter_horizontal for your Alliances
    filter_horizontal = ('red_teams', 'blue_teams')

    def is_played(self, obj):
        return obj.actual_time is not None
    is_played.boolean = True