from django.shortcuts import render



def home(request):
    return render(request, 'match/home.html')
    