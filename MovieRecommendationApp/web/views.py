from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q, Case, When, Count, Avg # Ensure Avg is imported
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Movie, Myrating, Feedback, Watchlist # Ensure all models are imported
from .forms import UserForm, FeedbackForm, ManualRecommendationForm, APIKeyForm
from .recommendation import Myrecommend # Ensure Myrecommend is imported
import numpy as np
import pandas as pd
import requests
import json
import os
from django.conf import settings
from django.contrib.auth.decorators import login_required


def landing_page(request):
    """Renders the new landing page and shows recent feedback."""
    latest_feedback = Feedback.objects.order_by('-created_at')[:3]
    context = {
        'feedbacks': latest_feedback
    }
    return render(request, 'web/landing.html', context)

def movie_list(request):
    """Renders the list of all movies with their average ratings and rating counts."""
    movies = Movie.objects.all()
    query = request.GET.get('q')
    if query:
        movies = movies.filter(Q(title__icontains=query)).distinct()

    # Annotate each movie with its average rating and count of ratings
    movies = movies.annotate(
        average_rating=Avg('myrating__rating'),
        rating_count=Count('myrating')
    )

    # If user is authenticated, fetch their personal rating for each movie efficiently
    user_personal_ratings = {}
    if request.user.is_authenticated:
        # Get a dictionary of {movie_id: rating} for the current user
        user_ratings_query = Myrating.objects.filter(user=request.user).values_list('movie_id', 'rating')
        user_personal_ratings = dict(user_ratings_query)

    context = {
        'movies': movies,
        'user_personal_ratings': user_personal_ratings, # Renamed for clarity in template
    }
    return render(request, 'web/list.html', context)

def detail(request, movie_id):
    if not request.user.is_authenticated:
        return redirect("login")
    
    movie = get_object_or_404(Movie, pk=movie_id)
    
    # Get overall average rating and count for the movie for display
    movie_with_stats = Movie.objects.filter(pk=movie_id).annotate(
        average_rating=Avg('myrating__rating'),
        rating_count=Count('myrating')
    ).first()

    # Get the current user's personal rating for THIS specific movie
    personal_rating = None
    if request.user.is_authenticated:
        try:
            personal_rating_obj = Myrating.objects.get(user=request.user, movie=movie)
            personal_rating = personal_rating_obj.rating
        except Myrating.DoesNotExist:
            pass # No personal rating for this movie yet

    if request.method == "POST":
        rate = request.POST.get('rating')
        if rate:
            Myrating.objects.update_or_create(
                user=request.user, movie=movie,
                defaults={'rating': float(rate)}
            )
            messages.success(request, "Your rating has been submitted!")
            # After rating submission, redirect to the detail page itself
            return redirect('detail', movie_id=movie.id)
    
    context = {
        'movies': movie, # The main movie object
        'movie_with_stats': movie_with_stats, # Movie object with average rating and count
        'personal_rating': personal_rating, # Current user's specific rating for this movie
    }
    return render(request, 'web/detail.html', context)


@login_required
def recommend(request):
    ai_movie_list = []
    user_ratings_exist = Myrating.objects.filter(user=request.user).exists()

    if not user_ratings_exist:
        messages.warning(request, "Please rate some movies to get personalized AI recommendations!")
        ai_movie_list = Movie.objects.annotate(num_ratings=Count('myrating')).order_by('-num_ratings')[:12]
    else:
        unique_rated_user_ids = Myrating.objects.values_list('user_id', flat=True).distinct().order_by('user_id')
        user_id_to_matrix_index = {user_id: idx for idx, user_id in enumerate(unique_rated_user_ids)}

        if request.user.id in user_id_to_matrix_index:
            current_user_matrix_index = user_id_to_matrix_index[request.user.id]
            
            prediction_matrix, Ymean = Myrecommend()

            if current_user_matrix_index < prediction_matrix.shape[1]:
                my_predictions = prediction_matrix[:, current_user_matrix_index] + Ymean.flatten()
                pred_idxs_sorted = np.argsort(my_predictions)[::-1] + 1
                
                rated_movie_ids = Myrating.objects.filter(user=request.user).values_list('movie_id', flat=True)
                recommended_movie_ids_filtered = [mid for mid in pred_idxs_sorted.tolist() if mid not in rated_movie_ids]

                preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(recommended_movie_ids_filtered)])
                ai_movie_list = Movie.objects.filter(id__in=recommended_movie_ids_filtered).order_by(preserved)[:12]
            else:
                messages.warning(request, "Cannot generate personalized AI recommendations based on your current ratings. Showing popular movies.")
                ai_movie_list = Movie.objects.annotate(num_ratings=Count('myrating')).order_by('-num_ratings')[:12]
        else:
            messages.warning(request, "Cannot generate personalized AI recommendations yet. Showing popular movies.")
            ai_movie_list = Movie.objects.annotate(num_ratings=Count('myrating')).order_by('-num_ratings')[:12]

    manual_movie_list = None
    form = ManualRecommendationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        rec_type = form.cleaned_data['recommendation_type']
        num_recs = form.cleaned_data['num_recommendations']

        if rec_type == 'movie':
            selected_movie = form.cleaned_data.get('movie')
            if selected_movie:
                manual_movie_list = Movie.objects.filter(genre=selected_movie.genre).exclude(id=selected_movie.id).order_by('?')[:num_recs]
            else:
                messages.error(request, "Please select a movie for movie-based recommendations.")
        elif rec_type == 'genre':
            selected_genre = form.cleaned_data.get('genre')
            if selected_genre:
                manual_movie_list = Movie.objects.filter(genre=selected_genre).order_by('?')[:num_recs]
            else:
                messages.error(request, "Please select a genre for genre-based recommendations.")

    context = {
        'form': form,
        'ai_movie_list': ai_movie_list,
        'manual_movie_list': manual_movie_list,
    }
    return render(request, 'web/recommend.html', context)


def signUp(request):
    form = UserForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        password = form.cleaned_data['password']
        user.set_password(password)
        user.save()
        user = authenticate(username=user.username, password=password)
        if user is not None:
            login(request, user)
            return redirect('landing_page')
    return render(request, 'web/signUp.html', {'form': form})

def Login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("landing_page")
        else:
            return render(request, 'web/login.html', {'error_message': 'Invalid Login'})
    return render(request, 'web/login.html')

def Logout(request):
    logout(request)
    return redirect("landing_page")

@login_required
def submit_feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('landing_page')
    else:
        form = FeedbackForm()
    return render(request, 'web/feedback.html', {'form': form})

@login_required
def trending(request):
    # Use Trakt API for trending movies
    trakt_client_id = os.environ.get('TRAKT_CLIENT_ID', '5ec622fbbdee1dc73c6dc8686a586f8c354912e2e21d639600df3fa78b279b4')  # Replace with your actual client ID or use env var
    youtube_api_key = os.environ.get('YOUTUBE_API_KEY', '')

    # Get user's API keys if they've set them (optional, for YouTube)
    if request.method == 'POST':
        form = APIKeyForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['youtube_api_key']:
                youtube_api_key = form.cleaned_data['youtube_api_key']
            messages.success(request, 'API keys updated successfully!')
    else:
        form = APIKeyForm()

    # Get trending movies from Trakt API
    trending_movies = []
    try:
        headers = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': trakt_client_id,
        }
        response = requests.get('https://api.trakt.tv/movies/trending', headers=headers)
        if response.status_code == 200:
            trakt_data = response.json()
            # Each item has 'movie' key with movie details
            trending_movies = [item['movie'] for item in trakt_data if 'movie' in item]
        else:
            try:
                error_data = response.json()
                error_message = error_data.get('error', response.text)
            except Exception:
                error_message = response.text
            messages.error(request, f'Trakt API error (status {response.status_code}): {error_message}')
    except Exception as e:
        messages.error(request, f'Error fetching trending movies from Trakt: {str(e)}')
    
    # Get user's watchlist
    watchlist = Watchlist.objects.filter(user=request.user)
    
    # Get recommendations based on watchlist (not implemented for Trakt in this patch)
    watchlist_recommendations = []
    
    context = {
        'trending_movies': trending_movies,
        'watchlist': watchlist,
        'watchlist_recommendations': watchlist_recommendations,
        'form': form,
        'youtube_api_key': youtube_api_key,
    }
    return render(request, 'web/trending.html', context)

@login_required
@require_POST
def add_to_watchlist(request):
    movie_id = request.POST.get('movie_id')
    movie_title = request.POST.get('movie_title')
    poster_path = request.POST.get('poster_path')
    
    if not movie_id or not movie_title:
        return JsonResponse({'status': 'error', 'message': 'Missing required data'})
    
    # Create or update watchlist entry
    watchlist_item, created = Watchlist.objects.update_or_create(
        user=request.user,
        movie_id=movie_id,
        defaults={
            'movie_title': movie_title,
            'poster_path': poster_path
        }
    )
    
    return JsonResponse({
        'status': 'success',
        'message': 'Added to watchlist',
        'created': created
    })

@login_required
@require_POST
def remove_from_watchlist(request):
    movie_id = request.POST.get('movie_id')
    
    if not movie_id:
        return JsonResponse({'status': 'error', 'message': 'Missing movie ID'})
    
    # Delete watchlist entry
    deleted, _ = Watchlist.objects.filter(user=request.user, movie_id=movie_id).delete()
    
    if deleted:
        return JsonResponse({'status': 'success', 'message': 'Removed from watchlist'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Movie not found in watchlist'})