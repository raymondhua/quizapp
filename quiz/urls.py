from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views


app_name = 'quiz'
urlpatterns = [
    path('<int:tournament_id>/<int:question_id>', views.questionPage, name='question'),
    path('<int:tournament_id>/<int:question_id>/result', views.answerPage, name='answer'),
    path('score', views.showHighScore, name='score'),
    path('users/<int:user_id>', views.showHighScore, name='score'),
    path('login', views.loginUser, name='login'),
    path('logout', views.logoutUser, name='logout'),
    path('register', views.registerUser, name='register'),
    path('delete', views.deleteUser, name='delete'),
    path('delete/<int:user_id>', views.deleteUser, name='delete'),
    path('create', views.createTournament, name='create'),
    path('users', views.usersPage, name='users'),
    path('all/<int:tournament_id>', views.showQuestions, name='all'),
    path('user', views.profilePage, name='profile'),
    path('', views.home, name='home'),
]