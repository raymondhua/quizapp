from django import forms
from .models import *
from datetime import date, timedelta

# Form when logging in
class LoginForm(forms.Form):
    username = forms.CharField(label='Enter username:')
    password = forms.CharField(label='Enter password:', widget=forms.PasswordInput())

# Form when a player wants to register
class RegisterForm(forms.Form):
    username = forms.CharField(label='Enter username:')
    firstName = forms.CharField(label='Enter first name:')
    lastName = forms.CharField(label='Enter last name:')
    password1 = forms.CharField(label='Enter password:', widget=forms.PasswordInput())
    password2 = forms.CharField(label='Enter password again:', widget=forms.PasswordInput())

# Form when they want to create a tournament
class CreateTournamentForm(forms.Form):
    dateNZFormat = '%d/%m/%Y'
    today = date.today().strftime(dateNZFormat)
    fortnightDate = date.today() + timedelta(days=14)
    fortnightFromToday = fortnightDate.strftime(dateNZFormat)
    name = forms.CharField(label='Enter name of tournament:')
    startDate = forms.DateField(initial=today, input_formats=[dateNZFormat], label='Enter start date with the format DD-MM-YYYY (e.g. 01/01/2000)')
    endDate = forms.DateField(initial=fortnightFromToday, input_formats=[dateNZFormat], label='Enter end date with the format DD-MM-YYYY (e.g. 31/12/2999):')
    categoryNo = forms.CharField(label='Select category type below:', widget=forms.Select(choices=Tournament().CATEGORIES))
    diffLevel = forms.CharField(label='Select difficulty level below:', widget=forms.Select(choices=Tournament().DIFFICULTYLEVEL))