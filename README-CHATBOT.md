# CineSuggest Chatbot Setup

## Overview
The CineSuggest chatbot is an AI-powered assistant that can provide information about movies and engage in general conversation. It uses Google's Gemini AI to provide movie information and engage in natural conversations.

## Installation

### 1. Install Dependencies
The chatbot requires several Python packages. Install them using pip:

```bash
pip install -r requirements-chatbot.txt
```

This will install:
- Django
- pandas, numpy, scipy (for the recommendation system)
- google-generativeai (for Gemini AI integration)

### 2. API Key
The chatbot requires an API key for Google AI. This should be configured in your Django settings file (`main/settings.py`):

```python
# API Keys
GOOGLE_AI_API_KEY = 'your_google_ai_api_key'
```

**IMPORTANT**: The current API key in the settings file has expired. You **must** obtain a new Google AI API key from the [Google AI Studio](https://makersuite.google.com/app/apikey) and replace it in the settings file for the chatbot to function properly.

### 3. Static Files
Make sure the static files are properly collected:

```bash
python manage.py collectstatic
```

## Usage

1. Start the Django development server:
```bash
python manage.py runserver
```

2. Navigate to the chatbot interface at: http://localhost:8000/chatbot/

3. You can ask the chatbot about movies or engage in general conversation.

## Troubleshooting

### Common Issues

1. **API Key Errors**: If you see error messages like "API key expired" or "You exceeded your current quota", you need to address API key issues:

   - When the API key is invalid or has quota issues, you will see fallback messages like "I'm having trouble connecting to my services right now" or "My movie recommendation service is temporarily unavailable" in the chat interface.
   - You **must** replace the API key in `settings.py` with a valid one from [Google AI Studio](https://makersuite.google.com/app/apikey).
   - After updating the API key, restart the Django server for the changes to take effect.

2. **Model Name Issues**: If you encounter errors about the model not being found (e.g., "models/gemini-pro is not found"), the model name format may need to be updated:

   - The chatbot uses the Gemini AI model, but the model names and formats can change.
   - Currently, the chatbot is configured to use `models/gemini-1.5-flash` which has higher quota limits.
   - If you encounter model-related errors, you may need to update the model name in `chatbot/bot.py`.
   - You can list available models by running a Python script with the Google AI library.

3. **Static Files Not Loading**: If the chat interface looks broken, make sure you've run `collectstatic` and that your static files settings are correct.

4. **Database Errors**: If you see database-related errors, make sure you've run migrations:
```bash
python manage.py migrate
```

### Fallback Responses

The chatbot is designed to provide helpful fallback responses when the API is not available. These responses are context-aware:

- For movie-related queries, it will acknowledge that the movie database is offline
- For general queries, it will provide a friendly message about the service being temporarily unavailable

### Debugging

If you encounter issues, check the Django development server console for error messages. The chatbot includes error handling that will log detailed information about any problems that occur.