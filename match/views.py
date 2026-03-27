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

        # Helper to process a specific phase (auto, p1, p2, etc.)
        def process_phase(phase_name, keys):
            # Convert values to int, treating missing as 0
            scores = [int(data.get(k, 0)) for k in keys]
            total = sum(scores)
            
            for i, team in enumerate(teams):
                score = scores[i]
                share = (score / total) if total > 0 else 0.0
                
                # This replaces all individual .create() calls
                TeamPeriodData.objects.create(
                    report=report,
                    team=team,
                    phase=phase_name,
                    score_value=score,
                    alliance_share=share, 
                    defended=data.get(f'{phase_name}_t{i+1}_def', False),
                    passed=data.get(f'{phase_name}_t{i+1}_pass', False)
                )

        # 3. Process All Phases
        # Auto
        process_phase('auto', [f'auto_t{i}_score' for i in range(1, 4)])
        # Tele-op Periods 1-6
        for p in range(1, 7):
            process_phase(f'p{p}', [f'p{p}_t{i}_score' for i in range(1, 4)])

        # 4. TOURNAMENT-AWARE NEXT MATCH LOGIC (Remains the same...)
        all_matches = list(Match.objects.filter(event=match.event))
        next_match = None
        try:
            current_index = all_matches.index(match)
            if current_index + 1 < len(all_matches):
                next_match = all_matches[current_index + 1]
        except ValueError:
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
            next_url = reverse('match:event_detail', kwargs={'event_key': match.event.key})

        return JsonResponse({
            "status": "success",
            "next_url": next_url,
            "message": f"Saved {match.verbose_name}."
        })

@login_required
def export_scout_data(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="scout_data_2026.csv"'

    writer = csv.writer(response)
    # Added 'Event' and 'EventKey' to the header
    writer.writerow([
        'Event', 'Match', 'Team', 'Phase', 'ScoreValue', 'AllianceShare%', 'Defended', 'Passed'
    ])

    data_points = TeamPeriodData.objects.select_related('report__match__event', 'team').all()

    for dp in data_points:
        # Convert 0.8 to "80.0%"
        share_percent = f"{dp.alliance_share * 100:.1f}%"
        
        writer.writerow([
            dp.report.match.event.name,
            dp.report.match.verbose_name,
            dp.team.team_number,
            dp.phase,
            dp.score_value,
            share_percent, # The new math column
            dp.defended,
            dp.passed
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
        return render(request, 'match/shutdown_confirm.html')
    
    return render(request, 'shutdown_button.html')