from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

class Movie(models.Model):
    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=100)
    movie_logo = models.FileField()

    def __str__(self):
        return self.title

class Myrating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.IntegerField(default=1, validators=[MaxValueValidator(5), MinValueValidator(0)])

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=1, validators=[MaxValueValidator(5), MinValueValidator(1)])
    comment = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Feedback from {self.user.username}'

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie_id = models.CharField(max_length=20)  # TMDB or OMDB movie ID
    movie_title = models.CharField(max_length=200)
    added_at = models.DateTimeField(default=timezone.now)
    poster_path = models.CharField(max_length=255, null=True, blank=True)  # Path to movie poster
    
    class Meta:
        unique_together = ('user', 'movie_id')  # Prevent duplicate entries
        ordering = ['-added_at']  # Most recently added first
    
    def __str__(self):
        return f'{self.user.username} - {self.movie_title}'

# --- ADD THESE TWO NEW MODELS FOR CHAT HISTORY ---
class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s session on {self.start_time.strftime('%Y-%m-%d')}"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    is_user = models.BooleanField(default=True)  # True for user, False for bot
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        sender = "User" if self.is_user else "Bot"
        return f"{sender}: {self.message_text[:30]}..."