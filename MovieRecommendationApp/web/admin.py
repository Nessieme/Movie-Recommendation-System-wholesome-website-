from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Avg
from .models import Movie, Myrating
from django.contrib.auth.models import User
from .models import Feedback, ChatSession, ChatMessage


# This is the custom view for our dashboard
def custom_admin_index(request, extra_context=None):
    # --- Data Gathering ---
    movie_count = Movie.objects.count()

    # NEW: Get count of all non-superuser users
    user_count = User.objects.filter(is_superuser=False).count()

    rating_count = Myrating.objects.count()
    average_rating = Myrating.objects.aggregate(avg=Avg('rating'))['avg'] or 0.0
    top_genres = Movie.objects.values('genre').annotate(movie_count=Count('id')).order_by('-movie_count')[:10]
    
    # Existing: Recent user ratings log (across all users) - still useful for recent activity
    user_ratings_log = Myrating.objects.select_related('user', 'movie').order_by('-id')[:10].values('user__username', 'movie__title', 'rating')

    # NEW: Get Top Active Non-Admin Users with their total ratings
    # Filters users who have made ratings and are not superusers
    # Annotates each with the count of their ratings
    # Orders by rating count (descending) and limits to top 5
    top_active_users = User.objects.filter(
        myrating__isnull=False, # Ensures we only consider users who have rated at least once
        is_superuser=False # Exclude superusers (admins)
    ).annotate(
        total_ratings_by_user=Count('myrating') # Count ratings per user
    ).order_by('-total_ratings_by_user')[:5] # Get top 5 by rating count


    # --- Progress Bar Calculation (already correctly placed in views.py) ---
    progress_val = rating_count
    progress_target = 1000 # Define your target number of ratings here

    if progress_target > 0:
        calculated_percentage = (progress_val / progress_target) * 100
        calculated_percentage = round(calculated_percentage, 0)
        if calculated_percentage > 100:
            calculated_percentage = 100
    else:
        calculated_percentage = 0

    # --- Context Dictionary ---
    context = {
        **admin.site.each_context(request),
        'title': 'Dashboard',
        'movie_count': movie_count,
        'user_count': user_count, # Updated user count (non-admin)
        'rating_count': rating_count,
        'average_rating': average_rating,
        'top_genres': top_genres,
        'user_ratings_log': user_ratings_log,
        'calculated_percentage': calculated_percentage,
        'top_active_users': top_active_users, # NEW: Add the list of top active users to context
    }

    if extra_context:
        context.update(extra_context)

    return render(request, "admin/index.html", context)

# This line tells the admin site to use our custom view for its main page.
admin.site.index = custom_admin_index

# (Keep your existing MovieAdmin and model registrations below this function as they are)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'genre')
    search_fields = ('title', 'genre')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('movie_report/', self.admin_site.admin_view(self.movie_report), name='movie_report'),
        ]
        return custom_urls + urls

    def movie_report(self, request):
        genre_data = Movie.objects.values('genre').annotate(
            movie_count=Count('id'),
            total_ratings=Count('myrating'),
            average_rating=Avg('myrating__rating')
        ).order_by('-movie_count')

        context = dict(
           self.admin_site.each_context(request),
           genre_data=genre_data,
        )
        return render(request, "admin/movie_report.html", context)

admin.site.register(Movie, MovieAdmin)
admin.site.register(Myrating)
admin.site.register(Feedback)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)