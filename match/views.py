from django.views.generic import TemplateView
from django.utils import timezone
from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from .models import Event, Match


class HomeView(TemplateView):
    # 1. This replaces: return render(request, "home.html", ...)
    template_name = 'match/home.html'

    # 2. This replaces the "context" dictionary you used to build manually
    def get_context_data(self, **kwargs):
        # First, call the original "recipe" to get the standard context
        context = super().get_context_data(**kwargs)
        
        # Now, add your custom "ingredients" (your filtered events)
        today = timezone.now().date()
        all_2026 = Event.objects.filter(year=2026).order_by('start_date')

        context['current_events'] = all_2026.filter(start_date__lte=today, end_date__gte=today)
        context['upcoming_events'] = all_2026.filter(start_date__gt=today)
        context['past_events'] = all_2026.filter(end_date__lt=today).order_by('-end_date')
        
        # 3. Return the full "suitcase" of data to the template
        return context




class EventDetailView(DetailView):
    model = Event
    template_name = 'match/event_detail.html'
    context_object_name = 'event'
    
    # This tells Django to look for the 'event_key' in the URL 
    # and match it to the 'key' field in your Event model
    pk_url_kwarg = 'event_key'

class ScoutFormView(TemplateView):
    template_name = 'match/scout_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Pulling match_key and alliance_color from the URL path
        match_key = self.kwargs.get('match_key')
        alliance_color = self.kwargs.get('alliance_color')
        
        match = get_object_or_404(Match, key=match_key)
        
        # Determine the target teams
        if alliance_color == 'red':
            teams = match.red_teams.all()
            alliance_class = 'text-danger'
        else:
            teams = match.blue_teams.all()
            alliance_class = 'text-primary'

        context.update({
            'match': match,
            'alliance_color': alliance_color,
            'alliance_class': alliance_class,
            'teams': teams,
            'neon_chartreuse': '#C8FF00', # Keeping the theme consistent
        })
        return context

    def post(self, request, *args, **kwargs):
        # This is where your scouting data processing will live
        # For now, we just re-render or redirect
        return self.get(request, *args, **kwargs)