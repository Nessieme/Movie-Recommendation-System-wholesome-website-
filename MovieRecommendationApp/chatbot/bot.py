# Simple chatbot implementation without chatterbot dependency
import google.generativeai as genai
from django.conf import settings
import traceback
import random

class SimpleChatBot:
    def __init__(self):
        # Configure the Gemini API
        try:
            genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
            # Using gemini-1.5-flash which has higher quota limits than gemini-1.5-pro
            # This should help avoid quota exceeded errors
            self.model = genai.GenerativeModel('models/gemini-1.5-flash')
            self.api_available = True
        except Exception as e:
            print(f"Error initializing Gemini API: {e}")
            self.api_available = False
    
    def get_response(self, input_text):
        # If API is not available, use fallback responses
        if not self.api_available:
            return self.get_fallback_response(input_text)
            
        try:
            # Test if the API is working
            test_response = self.model.generate_content("Hello")
            if not test_response or not hasattr(test_response, 'text'):
                raise Exception("API test failed - no valid response")
                
            # Phase 1: Use Gemini to extract the movie title from the user's query
            prompt = f"From the following text, extract only the movie title. If no movie title is mentioned, respond with 'NO_MOVIE'. Text: '{input_text}'"
            response = self.model.generate_content(prompt)
            movie_title = response.text.strip()

            if 'NO_MOVIE' in movie_title or not movie_title:
                # If no movie is found, fall back to a general conversation with Gemini
                response = self.model.generate_content(f"Answer this user query in a friendly, conversational way: {input_text}")
                return response.text

            # Phase 2: Use Gemini to get movie information directly
            movie_prompt = f"""
            Provide detailed information about the movie "{movie_title}" including:
            1. Plot summary
            2. Release year
            3. Main actors/actresses
            4. Director
            5. Genre
            6. Critical reception
            
            Format this as a friendly, conversational response as if you're recommending this movie to someone.
            If you're not sure about this specific movie, make it clear that you're providing general information
            that might not be completely accurate.
            """
            
            # Get movie information from Gemini
            movie_response = self.model.generate_content(movie_prompt)
            return movie_response.text

        except Exception as e:
            # Handle potential API errors gracefully
            print(f"Error in SimpleChatBot: {e}")
            print(traceback.format_exc())
            self.api_available = False  # Mark API as unavailable after an error
            return self.get_fallback_response(input_text)
    
    def get_fallback_response(self, input_text):
        """Provide a fallback response when the API is not available"""
        # Check if the input might be about movies
        movie_keywords = ['movie', 'film', 'watch', 'actor', 'actress', 'director', 'cinema', 'theater', 'plot', 'genre']
        
        if any(keyword in input_text.lower() for keyword in movie_keywords):
            movie_responses = [
                "I'd love to tell you about that movie, but my movie database is currently offline. Please try again later!",
                "I'm having trouble accessing my movie information right now. Can I help you with something else?",
                "My movie recommendation service is temporarily unavailable. Please check back soon!"
            ]
            return random.choice(movie_responses)
        else:
            general_responses = [
                "I'm sorry, I'm having trouble connecting to my knowledge base right now. Please try again later.",
                "I'd love to help, but I'm experiencing some technical difficulties at the moment. Can we try again in a bit?",
                "It seems my brain is taking a short break! I should be back to normal soon.",
                "I apologize for the inconvenience, but I'm unable to process your request right now. Please try again later."
            ]
            return random.choice(general_responses)

# Create a single instance of the chatbot
chatbot = SimpleChatBot()