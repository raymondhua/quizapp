from django.db import models
from django.contrib.auth.models import User

from datetime import date, timedelta

# Tournament model
class Tournament(models.Model):
    
    # Dynamic choices
    DIFFICULTYLEVEL = (
        ("0", 'Any difficulty'),
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )

    CATEGORIES = (
        ("0", 'Any category'),
        ('9', 'General Knowledge'),
        ('10', 'Books'),
        ('11', 'Film'),
        ('12', 'Music'),
        ('13', 'Musicals & Theatres'),
        ('14', 'Television'),
        ('15', 'Video Games'),
        ('16', 'Board Games'),
        ('17', 'Science & Nature'),
        ('18', 'Computers'),
        ('19', 'Mathematics'),
        ('20', 'Mythology'),
        ('21', 'Sports'),
        ('22', 'Geography'),
        ('23', 'History'),
        ('24', 'Politics'),
        ('25', 'Art'),
        ('26', 'Celebrities'),
        ('27', 'Animals'),
        ('28', 'Vehicles'),
        ('29', 'Comics'),
        ('30', 'Gadgets'),
        ('31', 'Japanese Anime & Manga'),
        ('32', 'Cartoon & Animations'),
    )
    name = models.CharField(max_length=25)
    start_date = models.DateField()
    end_date = models.DateField()
    category = models.CharField(max_length=2, choices=CATEGORIES, default="0")
    difficulty = models.CharField(max_length=6, choices=DIFFICULTYLEVEL, default="0")
    # checks if the tournament is upcoming
    def is_upcoming(self):
        today = date.today()
        return today < self.start_date
    # checks if the tournament is active
    def is_active(self):
        today = date.today()
        return self.start_date<=today and self.end_date>=today
    # checks if the tournament is in the past
    def start_is_past(self):
        today = date.today()
        return today > self.start_date
    # checks if the start date is less than equal to the end date
    def is_dates_correct(self):
        return self.start_date <= self.end_date

# Question model
class Question(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    question_no = models.IntegerField()
    question_text = models.TextField()

# Answer model
class Answer(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    question_no = models.IntegerField()
    correct_answer = models.TextField()
    incorrect_answers = models.TextField()
    # spits the incorrect answers string into an array
    def split_string(self):
        return self.incorrect_answers.split("|")

# Player progress model
class PlayerProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    question_no = models.IntegerField(default=1)
    score = models.IntegerField(default=0)

# Completed model
class Completed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    date = models.DateField()
    score = models.IntegerField()
    
