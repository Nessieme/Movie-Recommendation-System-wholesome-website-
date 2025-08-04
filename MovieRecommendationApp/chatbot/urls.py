

from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('session/<int:session_id>/', views.chat_view, name='chat_session'),
    path('new/', views.new_chat_session, name='new_chat'),
]