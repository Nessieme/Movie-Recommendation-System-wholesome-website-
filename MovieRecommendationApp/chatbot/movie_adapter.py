from chatterbot.logic import LogicAdapter
from django.conf import settings
import google.generativeai as genai
from tmdbv3api import TMDb, Movie

class MovieAdapter(LogicAdapter):
    def __init__(self, chatbot, **kwargs):
        super().__init__(chatbot, **kwargs)
        # Configure the APIs
        genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
        self.tmdb = TMDb()
        self.tmdb.api_key = settings.TMDB_API_KEY
        self.tmdb.language = 'en'
        self.model = genai.GenerativeModel('gemini-pro')

    def can_process(self, statement):
        # This adapter will try to process any statement
        return True

    def process(self, input_statement, additional_response_selection_parameters):
        from chatterbot.conversation import Statement

        try:
            # Phase 1: Use Gemini to extract the movie title from the user's query
            prompt = f"From the following text, extract only the movie title. If no movie title is mentioned, respond with 'NO_MOVIE'. Text: '{input_statement.text}'"
            response = self.model.generate_content(prompt)
            movie_title = response.text.strip()

            if 'NO_MOVIE' in movie_title or not movie_title:
                # If no movie is found, fall back to a general conversation with Gemini
                response = self.model.generate_content(f"Answer this user query in a friendly, conversational way: {input_statement.text}")
                return Statement(response.text)

            # Phase 2: Search for the movie on TMDb
            movie_search = Movie()
            results = movie_search.search(movie_title)

            if not results:
                return Statement(f"Sorry, I couldn't find any information about '{movie_title}'.")

            # Get details of the first result
            first_result = results[0]
            movie_details = movie_search.details(first_result.id)

            # Phase 3: Use Gemini to create a nice summary from the TMDb data
            summary_prompt = (
                f"Based on the following movie details, write a friendly and concise summary for a user. "
                f"Details: Title: {movie_details.title}, "
                f"Overview: {movie_details.overview}, "
                f"Release Date: {movie_details.release_date}, "
                f"Rating: {movie_details.vote_average:.1f}/10. "
                "Don't just list the facts; present them in a natural, conversational way."
            )
            final_response = self.model.generate_content(summary_prompt)
            
            response_statement = Statement(final_response.text)
            return response_statement

        except Exception as e:
            # Handle potential API errors gracefully
            print(f"Error in MovieAdapter: {e}")
            return Statement("I'm having a little trouble connecting to my services right now. Please try again in a moment.")