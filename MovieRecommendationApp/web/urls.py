from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('movies/', views.movie_list, name='movie_list'),
    path('movie/<int:movie_id>/', views.detail, name='detail'),
    path('signup/', views.signUp, name='signup'),
    path('login/', views.Login, name='login'),
    path('logout/', views.Logout, name='logout'),
    path('recommend/', views.recommend, name='recommend'),
    path('trending/', views.trending, name='trending'),
    path('watchlist/add/', views.add_to_watchlist, name='add_to_watchlist'),
    path('watchlist/remove/', views.remove_from_watchlist, name='remove_from_watchlist'),
    path('feedback/', views.submit_feedback, name='submit_feedback'),
]