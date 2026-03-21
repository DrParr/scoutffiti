from django.views.generic import TemplateView
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from .models import Event, Match, Team, MatchScoutReport, TeamPeriodData
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
import subprocess
import json
import csv



class HomeView(LoginRequiredMixin, TemplateView):
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


class EventDetailView(LoginRequiredMixin, DetailView):
    model = Event
    template_name = 'match/event_detail.html'
    context_object_name = 'event'
    
    # Use 'key' because that is your primary_key field name
    slug_field = 'key' 
    
    # Use 'event_key' because that is what you named it in urls.py
    slug_url_kwarg = 'event_key'


class ScoutFormView(LoginRequiredMixin, TemplateView):
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

def submit_scout(request, match_key, alliance_color):
    if request.method == "POST":
        data = json.loads(request.body)
        match = get_object_or_404(Match, key=match_key)
        
        # 1. Create the parent report
        report = MatchScoutReport.objects.create(
            scout=request.user,
            match=match,
            alliance_color=alliance_color
        )

        # 2. Get the teams in the alliance
        teams = match.get_teams_for_alliance(alliance_color)

        # 3. Save the data for all 3 teams
        for i, team in enumerate(teams, start=1):
            # Save Auto
            TeamPeriodData.objects.create(
                report=report,
                team=team,
                phase='auto',
                score_value=int(data.get(f'auto_t{i}_score', 0))
            )

            # Save 6 Tele-op Periods
            for p in range(1, 7):
                TeamPeriodData.objects.create(
                    report=report,
                    team=team,
                    phase=f'p{p}',
                    score_value=int(data.get(f'p{p}_t{i}_score', 0)),
                    defended=data.get(f'p{p}_t{i}_def', False),
                    passed=data.get(f'p{p}_t{i}_pass', False)
                )

        # 4. TOURNAMENT-AWARE NEXT MATCH LOGIC
        # We fetch all matches for the event. Because of our MatchManager, 
        # this list is ALREADY sorted: Quals 1-81 -> Semis -> Finals.
        all_matches = list(Match.objects.filter(event=match.event))
        next_match = None
        
        try:
            # Find the index of the current match in the sorted list
            current_index = all_matches.index(match)
            # If there's another match after this one, that's our "Next"
            if current_index + 1 < len(all_matches):
                next_match = all_matches[current_index + 1]
        except ValueError:
            # Fallback: if index fails, try to find the next number in the same level
            next_match = Match.objects.filter(
                event=match.event,
                comp_level=match.comp_level,
                match_number__gt=match.match_number
            ).first()

        # 5. Generate Redirect URL
        if next_match:
            next_url = reverse('match:scout_form', kwargs={
                'match_key': next_match.key, 
                'alliance_color': alliance_color
            })
        else:
            # End of the tournament! Send them to the event dashboard
            next_url = reverse('match:event_detail', kwargs={'event_key': match.event.key})

        return JsonResponse({
            "status": "success",
            "next_url": next_url,
            "message": f"Saved {match.verbose_name}. Moving to {next_match.verbose_name if next_match else 'Dashboard'}."
        })

@login_required
def export_scout_data(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="scout_data_2026.csv"'

    writer = csv.writer(response)
    # Added 'Event' and 'EventKey' to the header
    writer.writerow([
        'Event', 'EventKey', 'Match', 'Scout', 'Alliance', 
        'Team', 'Phase', 'ScoreValue', 'Defended', 'Passed', 'Timestamp'
    ])

    # select_related now goes 3 levels deep: Period -> Report -> Match -> Event
    data_points = TeamPeriodData.objects.select_related(
        'report__match__event', 'report__scout', 'team'
    ).all()

    for dp in data_points:
        writer.writerow([
            dp.report.match.event.name,
            dp.report.match.verbose_name,  # "Quals 1", "Finals 2", etc.
            dp.report.match.key,           # The technical key: "2026wiply_qm1"
            dp.report.scout.username,
            dp.report.alliance_color,
            dp.team.team_number,
            dp.phase,
            dp.score_value,
            dp.defended,
            dp.passed,
            dp.report.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    return response

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Log the user in automatically after sign-up
            return redirect('match:home')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

# Highly recommended: Only allow superusers to see/use this
@user_passes_test(lambda u: u.is_superuser)
def shutdown_pi(request):
    if request.method == 'POST':
        # Executes the system command
        subprocess.run(['sudo', '/sbin/shutdown', '-h', 'now'])
        return render(request, 'shutdown_confirm.html')
    
    return render(request, 'shutdown_button.html')