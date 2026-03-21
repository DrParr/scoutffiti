from django.contrib import admin, messages
from django.urls import path                # Added path
from django.http import HttpResponseRedirect # Added HttpResponseRedirect
from .models import District, Event, Team, Match
from django.db import transaction # Critical for data integrity

from match.services.blue_alliance_sync import BlueAllianceSync

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

# @admin.register(Match)
# class MatchAdmin(admin.ModelAdmin):
#     list_display = ('get_match_label', 'event', 'comp_level', 'match_number')
#     list_filter = ('event', 'comp_level')
#     search_fields = ('event__name', 'key')

#     def get_match_label(self, obj):
#         return f"{obj.comp_level.upper()} {obj.match_number}"
#     get_match_label.short_description = 'Match'

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    # Combined list display from both versions
    list_display = ('get_match_label', 'event', 'comp_level', 'match_number')
    list_filter = ('event', 'comp_level')
    search_fields = ('event__name', 'key')
    
    # Enable the custom button template
    change_list_template = "admin/match_change_list.html"

    def get_match_label(self, obj):
        return f"{obj.comp_level.upper()} {obj.match_number}"
    get_match_label.short_description = 'Match'

    # --- CUSTOM SYNC LOGIC ---

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # Note: self.admin_site.admin_view ensures permissions are checked
            path('fetch-data/', self.admin_site.admin_view(self.fetch_external_data), name='fetch_match_data'),
        ]
        return custom_urls + urls

    def fetch_external_data(self, request):
        """
        This is where your 'Dark Site' sync logic goes.
        For now, it's a placeholder that shows a success message.
        """
        try:
            sync = BlueAllianceSync()

            active_district_keys = list(District.objects.values_list('key', flat=True))

            for district_key in active_district_keys:
                sync.sync_district_events(district_key)
        
            active_event_keys = list(Event.objects.values_list('key', flat=True))
            for event_key in active_event_keys:
                sync.sync_matches(event_key)  

            
            messages.success(request, f"Successfully synced matches from local source.")
        except Exception as e:
            messages.error(request, f"Sync failed: {str(e)}")
            
        return HttpResponseRedirect("../")