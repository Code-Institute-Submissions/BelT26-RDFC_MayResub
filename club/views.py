from django.shortcuts import render, reverse, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.mail import send_mail
from .models import ClubMember, Match, MatchPlayer
from .forms import MatchForm

# Create your views here.


def index(request):
    """returns a view of the home page"""
    return render(request, 'club/index.html')



def next_fixture(request):
    member = request.user
    match_players = MatchPlayer.objects.all()
    if member in match_players:
        member.playing_match = True
    if Match.objects.filter(next_fixture=True).count() > 0:
        next_game = Match.objects.get(next_fixture=True)
    else:
        next_game = Match.objects.all().order_by('-match_date')[0] 
    blues = MatchPlayer.objects.filter(team='blue')
    whites = MatchPlayer.objects.filter(team='white')
    reserves = MatchPlayer.objects.filter(reserve=True)
    return render(request, 'club/next_fixture.html', {
        'next_game': next_game,
        'member': member,
        'blues': blues,
        'whites': whites, 
        'reserves': reserves       
    })


def league_table(request):
    member = request.user
    league_table = ClubMember.objects.filter(is_approved=True).order_by('-points', 'played')
    return render(request, 'club/league_table.html', {
        'league_table': league_table,
        'current_member': member,
    })


def results(request):
    past_results = Match.objects.filter(results_added=True)
    return render(request, 'club/results.html', {
        'past_results': past_results
    })


def book_match_place(request):
    match = Match.objects.get(registrations_open=True)
    registrations_open = False
    if match:
        registrations_open = True
    else:
        match = Match.objects.all().order_by('-match_date')[0]
    player = request.user
    try:
        player_reservation = MatchPlayer.objects.get(player_id=player)
    except:
        player_reservation = None
    if player_reservation:
        player.is_in_team = True
        player.save()
    else:
        player.is_in_team = False
        player.save()
    match_full = False
    registered_players = MatchPlayer.objects.filter(reserve=False)
    if registered_players.count() == 12:
        match_full = True
    return render(request, 'club/match_booking.html', {
        'player': player,
        'match': match,
        'registrations_open': registrations_open,
        'match_full': match_full,
    })


def confirm_availability(request):
    player = request.user
    match = Match.objects.get(registrations_open=True)
    player.is_available = True
    player.save()
    registered_players = MatchPlayer.objects.filter(match_id=match)
    num_registered_players = registered_players.count()
    if num_registered_players < 12:
        player.is_in_team = True
        player.save()
        new_player = MatchPlayer(player_id=player, match_id=match)
        new_player.save()
        messages.success(request, 'You have been allocated a place in '
                                  'the next match!')
    else:
        new_player = MatchPlayer(player_id=player, match_id=match, reserve=True)
        new_player.save()
        reserves = MatchPlayer.objects.filter(reserve=True)
        num_reserves = reserves.count()
        messages.success(request, 'You are number '
                                  f'{num_reserves} on the reserve list')                        
    return HttpResponseRedirect(reverse('index'))


def see_registered_players(request):
    players = MatchPlayer.objects.filter(reserve=False).order_by('-player_id__points', 'player_id__played')
    reserves = MatchPlayer.objects.filter(reserve=True)
    return render(request, 'club/see_players.html', {
        'players': players,
        'reserves': reserves,
    })


def cancel_match_place(request):
    player = request.user
    player.is_available = False
    player.save()
    if player.is_in_team is True:
        player.is_in_team = False
    match_player = MatchPlayer.objects.get(player_id=player)
    if match_player.reserve is False:
        send_mail('Player Cancellation',
                  f'{match_player.player_id} '
                  'has cancelled their place in the next match '
                  'Please reallocate the teams',
                  'management@rdfc.com',
                  ('helen.taylor@hotmail.it',))
    match_player.delete()
    messages.success(request, 'Your place has been cancelled')
    return HttpResponseRedirect(reverse('index'))


def applications(request):
    """ returns a template showing any pending applications and
    gives the manager the opportunity to approve them """
    pending_applications = ClubMember.objects.filter(is_approved=False)
    current_members = ClubMember.objects.filter(is_approved=True)
    return render(request, 'club/applications.html', {
        'pending_applications': pending_applications,
        'current_members': current_members
    })


def add_match(request):
    """returns a form in which the manager can add, remove
    or modify a match fixture"""
    if request.method == 'POST':
        form = MatchForm(request.POST)
        if form.is_valid():
            match = Match(
                match_date=form.cleaned_data['match_date'],
                time=form.cleaned_data['time'],
                location=form.cleaned_data['location'],
                blue_goals=form.cleaned_data['blue_goals'],
                white_goals=form.cleaned_data['white_goals'],
                results_added=form.cleaned_data['results_added']
            )
            match.save()
            messages.success(request, 'Match successfully added')
            return HttpResponseRedirect(reverse('index'))
    form = MatchForm()
    return render(request, 'club/add_fixture.html', {
        'form': form
    })


def select_match(request):
    matches = Match.objects.all().order_by('-match_date')
    return render(request, 'club/matches.html', {
        'matches': matches
    })


def update_player_score(request, pk):
    queryset = Match.objects.all()
    match = get_object_or_404(queryset, id=pk)
    all_players = MatchPlayer.objects.filter(match_id=match)
    blues = all_players.filter(team='blue')
    whites = all_players.filter(team='white')
    if match.blue_goals > match.white_goals:
        for player in blues:
            player.player_id__points += 3
            player.player_id__played += 1
            player.player_id__won += 1
            player.save()
        for player in whites:
            player.player_id__played += 1
            player.player_id__lost += 1
            player.save()
    elif match.white_goals > match.blue_goals:
        for player in whites:
            player.player_id__points += 3
            player.player_id__played += 1
            player.player_id__won += 1
            player.save()
        for player in blues:
            player.player_id__played += 1
            player.player_id__lost += 1
            player.save()
    else:
        for player in all_players:
            player.player_id__points += 1
            player.player_id__played += 1
            player.player_id__drawn += 1
            player.save()
    messages.success(request, 'Player scores updated')
    return HttpResponseRedirect(reverse('league-table'))


def edit_match(request, pk):
    queryset = Match.objects.all()
    match = get_object_or_404(queryset, id=pk)
    form = MatchForm(instance=match)
    
    if request.method == 'POST':
        form = MatchForm(request.POST, instance=match)
        if form.is_valid():
            match = Match(
                match_date=form.cleaned_data['match_date'],
                time=form.cleaned_data['time'],
                location=form.cleaned_data['location'],
                blue_goals=form.cleaned_data['blue_goals'],
                white_goals=form.cleaned_data['white_goals'],
                results_added=form.cleaned_data['results_added']
            )
            match.save()
            messages.success(request, 'Match successfully updated')
            return HttpResponseRedirect(reverse('index'))
  
    return render(request, 'club/add_fixture.html', {
        'form': form
    })


def delete_match(request, pk):
    """removes a match from the database"""
    queryset = Match.objects.all()
    match = get_object_or_404(queryset, id=pk)
    match.delete()
    messages.success(request, 'Match successfully deleted')
    return HttpResponseRedirect(reverse('select_match'))


def add_next(request, pk):
    """checks that there is not already a match flagged as
    the next fixture. Displays an error message if there is
    otherwise changes the next_fixture property of the match
    to true and updates the display in members.html"""
    next_match = Match.objects.filter(next_fixture=True)
    if len(next_match) > 0:
        current_fixture = Match.objects.get(next_fixture=True)
        messages.error(request, 'Only one match can be flagged as the next '
                                'fixtue. Please remove the next fixture flag'
                                f'from {current_fixture.match_date}')
        return HttpResponseRedirect(reverse('select_match'))
    queryset = Match.objects.all()
    match = get_object_or_404(queryset, id=pk)
    match.next_fixture = True
    match.save()
    messages.success(request, 'Next fixture updated')
    return HttpResponseRedirect(reverse('select_match'))


def remove_next(request, pk):
    queryset = Match.objects.filter(next_fixture=True)
    match = get_object_or_404(queryset, id=pk)
    match.next_fixture = False
    match.save()
    messages.success(request, 'Next fixture flag removed')
    return HttpResponseRedirect(reverse('select_match'))


def open_reg(request, pk):
    open_matches = Match.objects.filter(registrations_open=True)
    if len(open_matches) > 0:
        messages.error(request, 'Registrations can only be '
                                'open for one match at a time. '
                                'Please close registrations for any '
                                'open match before proceding.')
        return HttpResponseRedirect(reverse('select_match'))
    queryset = Match.objects.all()
    match = get_object_or_404(queryset, id=pk)
    match.registrations_open = True
    match.save()
    messages.success(request, "Registrations opened")
    members = ClubMember.objects.filter(is_approved=True)
    member_email_addresses = []
    for member in members:
        member_email_addresses.append(member.email)
    send_mail('Registrations Open!',
              f'Registrations for {match.match_date} have just opened!'
              ' Visit the club site to book your place.',
              'steve@rdfc.com',
               member_email_addresses)
    return HttpResponseRedirect(reverse('select_match'))


def close_reg(request, pk):
    queryset = Match.objects.all()
    match = get_object_or_404(queryset, id=pk)
    match.registrations_open = False
    match.save()
    messages.success(request, f"Registrations closed for {match.match_date}")
    return HttpResponseRedirect(reverse('select_match'))


def allocate_teams(request, pk):
    queryset = Match.objects.all()
    match = get_object_or_404(queryset, id=pk)
    registered_players = MatchPlayer.objects.filter(match_id=match, reserve=False)
    reserves = MatchPlayer.objects.filter(match_id=match, reserve=True).order_by('registration_time')
    while registered_players.count() < 12:
        if reserves.count() > 0:
            reserve_selected = reserves[0]
            reserve_selected.reserve = False
            reserve_selected.save()
            registered_players = MatchPlayer.objects.filter(match_id=match, reserve=False)
        else:
            messages.error(request, 'You require 12 available '
                                    'members to allocate teams')
            return HttpResponseRedirect(reverse('select_match'))
    reserves = MatchPlayer.objects.filter(match_id=match, reserve=True)
    blue_indices = [0, 3, 5, 7, 9, 11]
    white_indices = [1, 2, 4, 6, 8, 10]
    ordered_players = registered_players.order_by('-player_id__points', 'player_id__played', 'player_id__first_name')
    for index in blue_indices:
        blue = ordered_players[index]
        blue.team = 'blue'
        blue.save()
    for index in white_indices:
        white = ordered_players[index]
        white.team = 'white'
        white.save()
    messages.success(request, "Teams allocated")
    match.teams_allocated = True
    match.save()
    return HttpResponseRedirect(reverse('select_match'))


def reset_teams(request, pk):
    queryset = Match.objects.all()
    match = get_object_or_404(queryset, id=pk)
    registered_players = MatchPlayer.objects.filter(match_id=match)
    for player in registered_players:
        player.team = None
        player.save()
    messages.success(request, f"Teams cleared")
    match.teams_allocated = False
    match.save()
    return HttpResponseRedirect(reverse('select_match'))


def approve_member(request, pk):
    queryset = ClubMember.objects.filter(is_approved=False)
    member = get_object_or_404(queryset, id=pk)
    member.is_approved = True
    member.save()
    messages.success(request, 'Application approved')
    send_mail('Application approved',
              'Congratulations! '
              'Your application to join RDFC has been approved.'
              'We look forward to seeing you!', 
              'steve@rdfc.com',
              (member.email,))
    return HttpResponseRedirect(reverse('applications'))



def reject_member(request, pk):
    queryset = ClubMember.objects.filter(is_approved=False)
    member = get_object_or_404(queryset, id=pk)
    messages.success(request, 'Application rejected')
    send_mail('Application rejected',
              'Sorry. Your application to join RDFC has not been approved'
              'Please contact steve@rdfc for further information',
              'steve@rdfc.com',
              (member.email,))
    return HttpResponseRedirect(reverse('applications'))


def delete_member(request, pk):
    queryset = ClubMember.objects.filter(is_approved=True)
    member = get_object_or_404(queryset, id=pk)
    messages.success(request, 'Member deleted')
    member.delete()
    return HttpResponseRedirect(reverse('applications'))



