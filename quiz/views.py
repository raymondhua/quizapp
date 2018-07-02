# Project name:     Quiz Questions
# Name:             Raymond Hua
# Description:      Make a quiz app using the OpenTDB API
# Admin purpose:    Admin users can create tournaments with optional categories and difficultly levels, fetches the API and stores the questions and into the database. 
#                   They can also check high scores from all players and view all tournaments
# Player purpose:   The player answers 10 questions from a selected tournament, provides feedback if they are correct or not. They can also view their high scores. 
#                   They can check to see if they have any tournaments that are not completed
# Date:             22-06-2018

# Any superusers can be admin users

from django.shortcuts import render
from django.shortcuts import redirect, get_object_or_404

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import Http404
from django.urls import reverse
from django.template import context
import html.parser

from .models import *
from .forms import *

from random import shuffle
import requests
from datetime import date, timedelta

# Home screen displaying tournaments
# If it's an admin user, it would display all tournaments
# If it's a player, it would display active and upcoming tournaments
# If the user is not logged in, it redirects to the login page
@csrf_exempt
def home(request):
    if request.user.is_authenticated:
        today = date.today()
        allTournaments = Tournament.objects.all()
        activeTournaments = allTournaments.filter(start_date__lte=today, end_date__gte=today)
        upcomingTournaments = allTournaments.filter(start_date__gt=today)
        context = {}
        context['upcomingTournaments'] = upcomingTournaments
        if request.user.is_superuser:
            pastTournaments = allTournaments.filter(end_date__lt=today)
            context['allTournaments'] = allTournaments
            context['activeTournaments'] = activeTournaments
            context['pastTournaments'] = pastTournaments
            return render(request, 'admin/tournaments.html', context)
        else:
            completedTournament = Completed.objects.filter(user=request.user.id)
            playerProgress = PlayerProgress.objects.filter(user=request.user.id)
            completedIDs = completedTournament.values_list('tournament', flat=True) # List of ID's of completed tournaments of the user
            playerProgressIDs = playerProgress.values_list('tournament', flat=True) # List of ID's to saved tournaments (started the tournament but not finished with it)
            activeTournaments = activeTournaments.exclude(id__in=completedIDs) # Excludes all ID's from the list of completed tournaments
            activeTournaments = activeTournaments.exclude(id__in=playerProgressIDs) # Excludes all ID's from the list of saved tournaments
            savedTournaments = playerProgress
            context['savedTournaments'] = savedTournaments
            context['activeTournaments'] = activeTournaments
            return render(request, 'player/tournaments.html', context)
    else:
        return redirect('quiz:login')

# If it's an admin user, it would display all questions from a selected tournament
# Otherwise, it would raise a 404 error
@csrf_exempt
def showQuestions(request, tournament_id):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            today = date.today()
            tournament = get_object_or_404(Tournament, id=tournament_id)
            allTournaments = Answer.objects.filter(tournament=tournament)
            return render(request, 'admin/showQuestions.html', {'allQuestions': allTournaments, 'name': tournament.name})
        else:
            raise Http404
    else:
        raise Http404

# Question page for players
# Gets the question number and tournament id using arguments
@csrf_exempt
def questionPage(request, tournament_id, question_id):
    if not request.user.is_superuser:
        # If the error checking method is true it would display a 404 error
        if questionExists(request, tournament_id, question_id):
            raise Http404
        tournament = get_object_or_404(Tournament, id=tournament_id) #It ether gets an object or displays a 404 error
        question = get_object_or_404(Question, tournament=tournament, question_no=question_id)
        answer = get_object_or_404(Answer, question=question)
        # If the tournament is active it would display the questions and selected answers. Otherwise it would raise an 404 error
        if question.tournament.is_active():
            question = question.question_text
            correctAnswer = answer.correct_answer
            choices = answer.split_string() # Splits the string into array
            choices.append(correctAnswer) # appends the correct answer into the choice array
            shuffle(choices) # Shuffles all the choices otherwise the last choice would be the correct answer
            context = getContext(tournament.name, tournament_id, question_id)
            context['question'] = question
            context['choices'] = choices
            return render(request, 'player/question.html', context)
        else:
            raise Http404
    else:
        raise Http404

# Answer page for players
@csrf_exempt
def answerPage(request, tournament_id, question_id):
    # If they not selected a choice it would get them to go back to the question that they were
    if request.POST.get("answer")!=None:
        # If the error checking method is true it would display a 404 error
        # This is to see if they completed the tournament or try to access a question that they shouldn't be
        if questionExists(request, tournament_id, question_id):
            raise Http404
        player = get_object_or_404(User, id=request.user.id)
        tournament = get_object_or_404(Tournament, id=tournament_id)
        answer = get_object_or_404(Answer, tournament=tournament, question_no=question_id)
        score = 0
        if answer.tournament.is_active():
            # If the question submitted is question 1, it would create a PlayerProgress for the user logged in
            if question_id == 1:
                playerProgress = PlayerProgress(user=player, tournament=tournament)
                playerProgress.save()
            # If the question is less than equal to 10 it would run the code below
            if question_id <= 10:
                answer = Answer.objects.get(tournament=tournament, question_no=question_id)
                playerProgress = get_object_or_404(PlayerProgress, user=player, tournament=tournament)
                chosenAnswer = request.POST.get("answer")
                correctAnswer = answer.correct_answer
                playerProgress.question_no += 1 # Increments question number that they were by 1
                next_ID = playerProgress.question_no
                context = getContext(tournament.name, tournament_id, question_id)
                context['answer'] = correctAnswer
                context['nextID'] = next_ID
                # If the selected choice is correct, it would increment their score by 1
                # and displays to the user that they were correct
                if chosenAnswer==correctAnswer:
                    context['correctOrNot'] = "Correct"
                    playerProgress.score += 1
                # Otherwise, it would display to the user that they were wrong
                else:
                    context['correctOrNot'] = "Incorrect"
                playerProgress.save()
                score = playerProgress.score
                context['score'] = score
                # If they are finished with the game (other words, once they're at question 10) then...
                if question_id == 10:
                    completedTournament = Completed(user=player, tournament=tournament, date=date.today()) # Creates a completed model for the tournament and user
                    completedTournament.score = score  # uses the score from playerProgress
                    playerProgress.delete() # deletes the playerProgress model for the tournament and user
                    completedTournament.save() # and saves the completed model into the database
                return render(request, 'player/answer.html', context)
            else:
                raise Http404
    else:
        messages.error(request, "Must select a choice")
        return redirect(reverse('quiz:question', kwargs={'tournament_id': tournament_id, 'question_id': question_id}))

# Display users high scores
@csrf_exempt
def showHighScore(request, user_id=None):
    # If it's an admin user, it would show all high scores from any user using their ID...
    if request.user.is_superuser:
        # If it has an id number in the url /score, it would display all high scores from completed tournaments for a SELECTED user
        if user_id != None:
            completed = Completed.objects.filter(user=user_id)
            user = User.objects.get(id=user_id)
            return render(request, 'admin/playerProfile.html', {'completedTournaments': completed, 'user' : user})
        else:
            # If it has no id number in the url /score, it would display all high scores from completed for EVERY user group by their username alphabetically
            completed = Completed.objects.all().order_by('user')
            return render(request, 'admin/allPlayerScores.html', {'allCompletedTournaments': completed})
    # If the player is logged in, it would show all of their high scores
    elif request.user.is_authenticated:
        completed = Completed.objects.filter(user=request.user.id)
        return render(request, 'player/scoreHistory.html', {'completedTournaments': completed})
    # ...otherwise it would raise a 404 error
    else:
        raise Http404

# Login view
@csrf_exempt
def loginUser(request):
    # If the user is logged in, it would redirect them to the home page
    # Otherwise, this code would run below
    if not request.user.is_authenticated:
        # If the request method is POST, then it would run the code below
        # Otherwise, it would return the login form 
        if request.method == 'POST':
            form = LoginForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                user = authenticate(request, username=username, password=password) # Authenticates the user
                # If the user is found then it would login and redirects them to the home page
                if user is not None:
                    login(request, user) #Logs the user in
                    if request.user.is_superuser:
                        messages.success(request, "Hi "+request.user.username+", you are now logged in!!!")
                    else:
                        messages.success(request, "Hi "+request.user.first_name+", you are now logged in!!!")
                    return redirect('quiz:home')
                # If user is no match
                else:
                    # If the user doesn't exists, it would display so
                    if not User.objects.filter(username=username).exists():
                        return loginError(request, "ERROR: User doesn't exist", form)
                    # Otherwise, it would display incorrect password
                    else:
                        return loginError(request, "ERROR: Incorrect password", form)
            else:
                return loginError(request, "ERROR: Something is empty", form)
        else:
            form = LoginForm()
            return render(request, 'registration/login.html', {'form': form})
    else:
        return redirect('quiz:home')

# Logout view - for when the user presses the logout button
@csrf_exempt
def logoutUser(request):
    # If the user is logged in, it would run the logout method below
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "You are now logged out")
        form = LoginForm()
        return render(request, 'registration/login.html', {'form': form})
    # If not logged in, it would redirect them to the login page
    else:
        return redirect('quiz:login')

# Register view - when a player want's to register
@csrf_exempt
def registerUser(request):
    # If the user is not logged in, it would run the code below
    if not request.user.is_authenticated:
        # If the request method is POST then this method would run
        if request.method == 'POST':
            form = RegisterForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data["username"]
                password1 = form.cleaned_data["password1"]
                password2 = form.cleaned_data["password2"]
                # If the username doesn't exists, then this code would run below...
                # ...otherwise, it would display to the user that it exists
                if not User.objects.filter(username=username).exists():
                    # If both passwords match in the register form, it would create the user...
                    if password1==password2:
                        user = User.objects.create_user(username, None, password1)
                        user.first_name = form.cleaned_data["firstName"]
                        user.last_name = form.cleaned_data["lastName"]
                        user.save()
                        messages.success(request, "User created!!!")
                        return redirect('quiz:login')
                    # ...otherwise, it would display to the user that they don't match
                    else:
                        return registerError(request, "ERROR: Passwords don't match", form)
                else:
                    return registerError(request, "ERROR: User exists", form)
            else:
                return registerError(request, "ERROR: Something is empty", form)
        else:
            form = RegisterForm()
            return render(request, 'registration/register.html', {'form': form})
    else:
        raise Http404

# Delete user method - for when the Admin wants to delete a player
# Or a player to delete themselves
@csrf_exempt
def deleteUser(request, user_id=None):
    # If the request method is GET, it would show the deletion page
    # Elsewise - it would process the deletion form
    if request.method == 'GET':
        if request.user.is_authenticated:
            if request.user.is_superuser:
                user = get_object_or_404(User, id=user_id)
                return render(request, 'admin/delete.html', {'user': user})
            else:
                user = get_object_or_404(User, id=request.user.id)
                return render(request, 'player/delete.html', {'user': user})
    else:
        if request.user.is_authenticated:
            if request.user.is_superuser:
                user = get_object_or_404(User, id=user_id)
                username = user.username
                user.delete() # this is to delete the certian user from the database
                messages.success(request, "User: "+username+" deleted!!!")
                return redirect('quiz:users')
            else:
                user = get_object_or_404(User, id=request.user.id)
                user.delete()
                messages.success(request, "Your account was deleted!!!")
                return redirect('quiz:login')
    raise Http404

# Method for when the admin user creates a tournament
@csrf_exempt
def createTournament(request):
    # If the user logged in is an admin user then it would fall in the code below
    # If it's not a admin user it would show a 404 error
    if request.user.is_superuser:
        # If the request method is GET, then it would show the create tournament form
        if request.method == 'GET':
            form = CreateTournamentForm()
            return render(request, 'admin/createTournament.html', {'form': form})
        # Otherwise it would processes the form information
        else:
            form = CreateTournamentForm(request.POST)
            if form.is_valid():
                tournament = Tournament()
                tournament.name = form.cleaned_data["name"]
                tournament.start_date = form.cleaned_data["startDate"]
                tournament.end_date = form.cleaned_data["endDate"]
                # If the dates are correct or the start date in the past (or both), it would return the form information and display an error of what's wrong
                if not tournament.is_dates_correct() or tournament.start_is_past():
                    if tournament.start_is_past():
                        messages.error(request, "ERROR: Start date must not in the past")
                    elif not tournament.is_dates_correct():
                        messages.error(request, "ERROR: Dates must be correct")
                    return render(request, 'admin/createTournament.html', {'form':form})
                tournament.category = form.cleaned_data["categoryNo"]
                tournament.difficulty = form.cleaned_data["diffLevel"]
                objectData = getAPI(tournament.category, tournament.difficulty) # Gets the api from the getAPI method (below this method)
                # If the api response code returns anything other than 0 it would display to the user that no questions are found
                if objectData["response_code"] != 0:
                    messages.error(request, "ERROR: No questions found")
                    return render(request, 'admin/createTournament.html', {'form':form})
                tournament.save()
                quizData = objectData['results']
                count = 1 # initializes question number count (e.g. 1 as in question 1)
                for quiz in quizData:
                    html_parser = html.parser.HTMLParser()
                    question = Question() # creates Question instance
                    question.tournament = tournament # passes in tournament
                    question.question_no = count
                    question.question_text = html_parser.unescape(quiz['question']) # stores the question in question_text
                    answer = Answer() # creates Answer instance
                    answer.tournament = tournament
                    answer.question_no = count
                    answer.correct_answer = html_parser.unescape(quiz['correct_answer']) # stores the correct answer in correct_answer
                    answer.incorrect_answers = '|'.join(map(str, html_parser.unescape(quiz['incorrect_answers']))) # converts the incorrect answer array into a string separated by a pipe (|)
                    question.save()
                    answer.question = question
                    answer.save()
                    count +=1 # increments count 
                messages.success(request, 'Tournament "'+ tournament.name + '" created!!!')
                return redirect('quiz:home')
            else:
                return render(request, 'admin/createTournament.html', {'form': form})
    else:
        raise Http404


# Gets the API from OpenTDB
def getAPI(categoryCode="0", difficultyCode="0"):
    linkToAPI = None
    # If the user selected a category AND difficulty level, it would run this link below
    if categoryCode != "0" and difficultyCode != "0":
        linkToAPI = "https://opentdb.com/api.php?amount=10&category=%s&difficulty=%s" % (categoryCode, difficultyCode)
    # If the user selected a category, it would run this link below
    elif categoryCode != "0":
        linkToAPI = "https://opentdb.com/api.php?amount=10&category=%s" % (categoryCode)
    # If the user selected a difficulty level, it would run this link below
    elif difficultyCode != "0":
        linkToAPI = "https://opentdb.com/api.php?amount=10&difficulty=%s" % (difficultyCode)
    # If the user DIDN'T select a category OR difficulty level, it would run this link below
    else:
        linkToAPI = "https://opentdb.com/api.php?amount=10"
    response = requests.get(linkToAPI)
    api = response.json()
    return api

# Admin page showing all players
@csrf_exempt
def usersPage(request):
    # If logged in as a admin user, it would display all completed scores from all tournaments for every user
    if request.user.is_superuser:
        user = User.objects.exclude(is_superuser=True)
        return render(request, 'admin/allUsers.html', {'users': user})
    else:
        raise Http404

# Profile page for the player
@csrf_exempt
def profilePage(request):
    # If the user is logged in
    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        return render(request, 'player/profile.html', {'user': user})
    else:
        raise Http404

# If the user makes an error in the register screen then it would return this method - reduce code duplication 
# Returns register screen with an error of what's wrong
def registerError(request, message, form=None):
    messages.error(request, message)
    return render(request, 'registration/register.html', {'form': form})

# If the user makes an error in the login screen then it would return this method - reduce code duplication 
# Returns login screen with an error of what's wrong
def loginError(request, message, form=None):
    messages.error(request, message)
    return render(request, 'registration/login.html', {'form': form})

# Error checking method
def questionExists(request, tournament_id, question_id):
    # If the player is finished with the tournament, it would return true
    if Completed.objects.filter(user=request.user.id, tournament=tournament_id).exists():
        return True
    else:
        playerProgress = PlayerProgress.objects.filter(user=request.user.id, tournament=tournament_id) # Gets the object
        # If the player progress exists it would return true...
        if playerProgress.exists():
            # They are on any other question than they one they should be, it returns True
            if question_id != playerProgress[0].question_no:
                return True
        else:
            # ...otherwise, if they not started it and if they are not on question 1 (which is where they should be), it returns True
            if question_id != 1:
                return True
        return False

#Method to return context with the tournamentName tournamentID and question number
def getContext(tournamentName, tournamentID, questionNumber):
    context = {}
    context['name'] = tournamentName
    context['questionID'] = questionNumber
    context['tournamentID'] = tournamentID
    return context

# ---Errors - Have DEBUG = on and ALLOWED_HOSTS=['*'] in settings.py---
# ---DON'T UNCOMMENT IT---

# def error404(request):
#         context = {}
#         return render(request,'error404.html', context)
 
# def error500(request):
#         context = {}
#         return render(request,'error500.html', context)

