from django import forms
from django.contrib.auth.models import User
from .models import Feedback, Movie, Watchlist  # Import the Feedback, Movie, and Watchlist models

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 8, 'placeholder': 'Tell us what you think...'}),
        }

class APIKeyForm(forms.Form):
    omdb_api_key = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your OMDB API key'}),
        help_text='Get your API key from https://www.omdbapi.com/apikey.aspx'
    )
    youtube_api_key = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your YouTube API key'}),
        help_text='Get your API key from https://console.developers.google.com/'
    )

# --- ADD THIS NEW FORM AT THE END ---
class ManualRecommendationForm(forms.Form):
    # Field for selecting recommendation type (Movie or Genre)
    recommendation_type = forms.ChoiceField(
        choices=[('movie', 'Movie Based'), ('genre', 'Genre Based')],
        label="Select Recommendation Type"
    )

    # Field for selecting a specific movie
    movie = forms.ModelChoiceField(
        queryset=Movie.objects.order_by('title'),
        required=False,
        label="Select Movie"
    )

    # Field for selecting a genre
    genre = forms.ChoiceField(
        choices=[],  # We will populate this dynamically in the view
        required=False,
        label="Select Genre"
    )

    # Field for number of recommendations
    num_recommendations = forms.IntegerField(
        min_value=5,
        max_value=20,
        initial=10,
        label="Number of movies you want Recommended"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get all unique genres from the Movie model
        genres = Movie.objects.values_list('genre', flat=True).distinct().order_by('genre')
        self.fields['genre'].choices = [('', '--Select--')] + [(g, g) for g in genres if g]