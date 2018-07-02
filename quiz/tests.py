# This unit test file is to see if...
# The models are correct
# The site can run as an admin and player user
# Successfully creating the tournaments from the view function and checking to see if they are active

from django.test import TestCase
from datetime import date, timedelta

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User

from .models import *
from .views import getAPI
from .forms import *

from django.contrib import auth

import logging
logger = logging.getLogger(__name__)

# STATUS CODES
# 404 - error
# 302 - redirect
# 200 - page loading from method

# Testing the tournament models and their dates are past, active, upcoming and checks if dates are correct
class TournamentModelTest(TestCase):
    # Creates tournaments using different dates
    def setUp(self):
        self.twoWeeksAgo = date.today() - timedelta(days=14)
        self.weekAgo = date.today() - timedelta(days=7)
        self.today = date.today()
        self.weekFromToday = date.today() + timedelta(days=7)
        self.fortnightFromNow = date.today() + timedelta(days=14)
        Tournament.objects.create(start_date=self.twoWeeksAgo, end_date=self.weekAgo) # Creates past tournament
        Tournament.objects.create(start_date=self.weekAgo, end_date=self.weekFromToday) # Creates active tournament
        Tournament.objects.create(start_date=self.weekFromToday, end_date=self.fortnightFromNow) # Creates future tournament
        Tournament.objects.create(start_date=self.weekAgo, end_date=self.twoWeeksAgo) # Creates mixed date tournament
        Tournament.objects.create(start_date=self.today, end_date=self.fortnightFromNow) # Creates tournament that starts today
        Tournament.objects.create(start_date=self.weekAgo, end_date=self.today) # Creates tournament that is ends today

    # Testing to see if one of the tournament objects is in the past
    def test_is_past(self):
        tournament = Tournament.objects.get(start_date=self.weekFromToday, end_date=self.fortnightFromNow)
        self.assertIs(tournament.is_upcoming(), True)

    # Testing to see if one of the tournament objects is active
    def test_is_active(self):
        tournament = Tournament.objects.get(start_date=self.weekAgo, end_date=self.weekFromToday)
        self.assertIs(tournament.is_active(), True)

    # Testing to see if one of the tournament objects is upcoming
    def test_is_upcoming(self):
        tournament = Tournament.objects.get(start_date=self.weekFromToday, end_date=self.fortnightFromNow)
        self.assertIs(tournament.is_upcoming(), True)
    
    # Testing to see if one of the tournament objects has the dates correct (the start date is always before or on the end date)
    def test_dates_correct(self):
        tournament = Tournament.objects.get(start_date=self.weekFromToday, end_date=self.fortnightFromNow)
        self.assertIs(tournament.is_dates_correct(), True)
        
    # Testing to see if one of the tournament objects has the dates incorrect
    def test_dates_incorrect(self):
        tournament = Tournament.objects.get(start_date=self.weekAgo, end_date=self.twoWeeksAgo)
        self.assertIs(tournament.is_dates_correct(), False)
    
# Testing the API link to see if it's correct and also checks the categories, difficulty levels and number of questions are correct
class APITest(TestCase):
    #API testing method - check if the API links work
    def apiTesting(self, categoryCode="0", difficultyCode="0"):
        linkToAPI = None
        if categoryCode != "0" and difficultyCode != "0":
            linkToAPI = "https://opentdb.com/api.php?amount=10&category=%s&difficulty=%s" % (categoryCode, difficultyCode)
        elif categoryCode != "0":
            linkToAPI = "https://opentdb.com/api.php?amount=10&category=%s" % (categoryCode)
        elif difficultyCode != "0":
            linkToAPI = "https://opentdb.com/api.php?amount=10&difficulty=%s" % (difficultyCode)
        else:
            linkToAPI = "https://opentdb.com/api.php?amount=10"
        return linkToAPI

    # Test if the category and difficulty level returns the first if statement
    def test_category_difficulty_link(self):
        expectedAPILink = "https://opentdb.com/api.php?amount=10&category=15&difficulty=medium"
        self.assertEqual(self.apiTesting('15','medium'), expectedAPILink)

    # Test if the category number returns the first if else statement
    def test_category_link(self):
        expectedAPILink = "https://opentdb.com/api.php?amount=10&category=15"
        self.assertEqual(self.apiTesting('15'), expectedAPILink)

    # Test if the difficulty level returns the second if else statement
    def test_difficulty_link(self):
        expectedAPILink = "https://opentdb.com/api.php?amount=10&difficulty=medium"
        self.assertEqual(self.apiTesting('0','medium'), expectedAPILink)

    # Test if the with no arguments it should return the else statement
    def test_link(self):
        expectedAPILink = "https://opentdb.com/api.php?amount=10"
        self.assertEqual(self.apiTesting(), expectedAPILink)

    # Test if the category in the API is General Knowledge
    def test_category_level(self):
        apiFunction = getAPI("9") #9 is General Knowledge in OpenTDB
        quizData = apiFunction['results']
        getFirstObject = quizData[1]
        self.assertEqual(getFirstObject['category'], 'General Knowledge')

    # Test if the difficulty level in the API is medium
    def test_difficulty_level(self):
        apiFunction = getAPI("9", "medium")
        quizData = apiFunction['results']
        getFirstObject = quizData[1]
        self.assertEqual(getFirstObject["difficulty"], 'medium')

    # Test if the difficulty level in the API is medium - with no category is passed in
    def test_difficulty_level_2(self):
        apiFunction = getAPI("0", "medium")
        quizData = apiFunction['results']
        getFirstObject = quizData[1]
        self.assertEqual(getFirstObject["difficulty"], 'medium')

    # Test if the difficulty level in the API is easy
    def test_difficulty_level_3(self):
        apiFunction = getAPI("9", "easy")
        quizData = apiFunction['results']
        getFirstObject = quizData[1]
        self.assertEqual(getFirstObject["difficulty"], 'easy')

    # Test if the API has ten questions
    def test_ten_questions(self):
        apiFunction = getAPI()
        quizData = apiFunction['results']
        noOfQuestions = len(quizData)
        self.assertEqual(noOfQuestions, 10)

# Testing the incorrect answers
class AnswerTest(TestCase):
    # Testing if the array converts to a string successfully
    def test_convert_array_to_string(self):
        answerArray = ["Oh yeeaaah!","Whoa there!","Nyeh heh heh!"]
        incorrect_answers = '|'.join(map(str, answerArray))
        expectedString = "Oh yeeaaah!|Whoa there!|Nyeh heh heh!"
        self.assertEqual(incorrect_answers, expectedString)
    
    # Testing if the string converts to a array successfully
    def test_convert_string_to_array(self):
        stringArray = "Oh yeeaaah!|Whoa there!|Nyeh heh heh!"
        incorrectAnswers = stringArray.split("|")
        expectedArray = ["Oh yeeaaah!","Whoa there!","Nyeh heh heh!"]
        self.assertEqual(incorrectAnswers, expectedArray)

# Checks the Login screen
class LoginTest(TestCase):
    # Sets up the client
    def setUp(self):
        self.client = Client()

    # Tests if the login page exists - with hard-coding
    def test_login_exists_hardcode(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)

    # Tests if the login page exists - using the reverse function
    def test_login_exists(self):
        response = self.client.get(reverse('quiz:login'))
        self.assertEqual(response.status_code, 200)

    # Tests if the home page redirects to the login screen
    def test_home_redirects(self):
        response = self.client.get(reverse('quiz:home'))
        self.assertEqual(response.status_code, 302)
        
    # Tests if a logged-in only page is 404
    def test_page_is_404(self):
        response = self.client.get(reverse('quiz:create'))
        self.assertEqual(response.status_code, 404)

# Testing the Register section
class RegisterTest(TestCase):
    def setUp(self):
        self.client = Client()
    # Tests if the register page exists
    def test_reg_user(self):
        response = self.client.get(reverse('quiz:register'))
        self.assertEqual(response.status_code, 200)
    # Tests if the form submitted is the wrong password and returning with the method saying so
    def test_incorrect_password(self):
        formData = {'username': 'testuser', 'firstName': 'Test','lastName': 'User','password1': 'P@ssw0rd','password2': 'P@ssw0rd1'}
        response = self.client.post(reverse('quiz:register'), formData)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(messages[0]), "ERROR: Passwords don't match")
    # Tests if the form submitted has - should return an error saying it's missing something (username)
    def test_form_not_valid(self):
        formData = {'username': '', 'firstName': 'Test','lastName': 'User','password1': 'P@ssw0rd','password2': 'P@ssw0rd1'}
        response = self.client.post(reverse('quiz:register'), formData)
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), "ERROR: Something is empty")
    # Tests if the form submitted two times - should return if the user exists
    def test_user_exists(self):
        formData = {'username': 'testuser', 'firstName': 'Test','lastName': 'User','password1': 'P@ssw0rd','password2': 'P@ssw0rd'}
        response = self.client.post(reverse('quiz:register'), formData, follow=True)
        response = self.client.post(reverse('quiz:register'), formData)
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), "ERROR: User exists")
    # Tests if the form submitted and should return the user is created
    def test_user_created(self):
        formData = {'username': 'testuser', 'firstName': 'Test','lastName': 'User','password1': 'P@ssw0rd','password2': 'P@ssw0rd'}
        response = self.client.post(reverse('quiz:register'), formData)
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('quiz:login'))
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), "User created!!!")

# This method is to test the site as a PLAYER user
class PlayerSiteTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'player'
        formData = {'username': self.username, 'firstName': 'Test','lastName': 'User','password1': 'P@ssw0rd','password2': 'P@ssw0rd'}
        response = self.client.post(reverse('quiz:register'), formData, follow=True)
        self.credentials = {'username': self.username,'password': 'P@ssw0rd'}
        self.login = self.client.post(reverse('quiz:login'), self.credentials, follow=True)
        self.user = User.objects.get(username=self.login.context['user'].username)
    # Testing to see if the login is successful
    def test_login_as_player(self):
        response = self.client.get(reverse('quiz:home'))
        self.assertEqual(self.user.username, self.username)
        self.assertTrue(self.login.context['user'].is_active)
    # Testing if the login page redirects to the home page
    def test_redirect(self):
        response = self.client.get(reverse('quiz:login'))
        self.assertEqual(response.status_code, 302)
    # Testing if home page exists with no errors or redirects
    def test_home(self):
        response = self.client.get(reverse('quiz:home'))
        self.assertEqual(response.status_code, 200)
    # Tests if player user tries to access an admin user page - should return 404 error
    def test_404_on_admin_page(self):
        response = self.client.get(reverse('quiz:create'))
        self.assertEqual(response.status_code, 404)
    # Tests if player user is deleted
    def test_user_deleted(self):
        response = self.client.post(reverse('quiz:delete'), follow=True)
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), "Your account was deleted!!!")
        self.assertEqual(response.status_code, 200)

# This method is to test the site as a ADMIN user
class AdminSiteTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'admin'
        self.credentials = {'username': self.username,'password': 'hello'}
        user = User.objects.create_superuser(username=self.username, email=None, password='hello') # Creates admin user
        self.login = self.client.post(reverse('quiz:login'), self.credentials, follow=True) # Logs in as admin user
        self.user = User.objects.get(username=self.login.context['user'].username)
    # Check if the admin user is logged in
    def test_login_as_admin(self):
        response = self.client.get(reverse('quiz:home'))
        self.assertEqual(self.user.username, self.username)
        self.assertTrue(self.login.context['user'].is_active)
    # Tests home page loads successfully from the home method (no errors or redirects)
    def test_home(self):
        response = self.client.get(reverse('quiz:home'))
        self.assertEqual(response.status_code, 200)
    # Testing if creating tournament works
    def test_create_tournament(self):
        dateNZFormat = '%d/%m/%Y'
        today = date.today().strftime(dateNZFormat)
        week = date.today() + timedelta(days=7)
        weekFromToday = week.strftime(dateNZFormat)
        formData = {'name': 'test', 'startDate': today,'endDate': weekFromToday,'categoryNo': '0','diffLevel': '0'}
        response = self.client.post(reverse('quiz:create'), formData)
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('quiz:home'))
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), 'Tournament "test" created!!!')
        self.assertGreater(len(response.context['activeTournaments']), 0)
        self.assertEqual(response.status_code, 200)

# Testing the site automatically
# Creates tournaments and fetches the API
# Logs out and create and log in as player
class AutomatedTestSite(TestCase):
    def setUp(self):
        self.client = Client()
        self.adminUsername = 'admin'
        self.playerUsername = 'player'
        self.credentials = {'username': self.adminUsername,'password': 'hello'}
        user = User.objects.create_superuser(username=self.adminUsername, email=None, password='hello') # Creates admin user
        self.login = self.client.post(reverse('quiz:login'), self.credentials, follow=True) # Logs in as admin user
        dateNZFormat = '%d/%m/%Y'
        today = date.today().strftime(dateNZFormat)
        week = date.today() + timedelta(days=7)
        weekFromToday = week.strftime(dateNZFormat)
        formData = {'name': 'test', 'startDate': today,'endDate': weekFromToday,'categoryNo': '0','diffLevel': '0'}
        response = self.client.post(reverse('quiz:create'), formData)
        response = self.client.get(reverse('quiz:logout')) # Logs out of admin user
        loginData = {'username': self.playerUsername, 'firstName': 'Test','lastName': 'User','password1': 'P@ssw0rd','password2': 'P@ssw0rd'} #form
        response = self.client.post(reverse('quiz:register'), loginData, follow=True) # Registers player using the form above
        credentials = {'username': self.playerUsername,'password': 'P@ssw0rd'}
        self.login = self.client.post(reverse('quiz:login'), credentials, follow=True) # Logs in as player
        self.user = User.objects.get(username=self.login.context['user'].username)
    # Test if it's logged in as player
    def test_login_as_player(self):
        self.assertTrue(self.login.context['user'].is_active)
        response = self.client.get(reverse('quiz:home'))
        self.assertEqual(self.user.username, self.playerUsername)
    # Test if it's home page loads successfully from the home method
    def test_home(self):
        response = self.client.get(reverse('quiz:home'))
        self.assertEqual(response.status_code, 200)
    # Test if an active tournament context exists
    def test_activeTournaments_exists(self):
        response = self.client.get(reverse('quiz:home'))
        self.assertGreater(len(response.context['activeTournaments']), 0)