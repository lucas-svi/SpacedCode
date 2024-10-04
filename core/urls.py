# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('add/', views.add_question, name='add_question'),
    path('edit/<int:pk>/', views.edit_question, name='edit_question'),
    path('delete/<int:pk>/', views.delete_question, name='delete_question'),
    path('review/<int:pk>/', views.review_question, name='review_question'),
    path('statistics/', views.statistics, name='statistics'),
]
