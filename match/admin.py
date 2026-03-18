from django.contrib import admin
from .models import District, Event, Team, Match

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'key', 'abbreviation')
    search_fields = ('display_name', 'key')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'city', 'week', 'start_date', 'event_type_string')
    list_filter = ('year', 'week', 'district', 'event_type_string')
    search_fields = ('name', 'short_name', 'city', 'key')

    # This allows you to see the District name even though it's a ForeignKey
    def get_district_name(self, obj):
        return obj.district.display_name if obj.district else "No District"
    get_district_name.short_description = 'District'

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('team_number', 'nickname', 'city', 'state_prov')
    list_filter = ('state_prov',)
    search_fields = ('team_number', 'nickname', 'city')
    ordering = ('team_number',)

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('get_match_label', 'event', 'comp_level', 'match_number')
    list_filter = ('event', 'comp_level')
    search_fields = ('event__name', 'key')

    def get_match_label(self, obj):
        return f"{obj.comp_level.upper()} {obj.match_number}"
    get_match_label.short_description = 'Match'