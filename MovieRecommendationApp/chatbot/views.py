from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from web.models import ChatSession, ChatMessage
from .bot import chatbot
import traceback

@login_required
def chat_view(request, session_id=None):
    user = request.user
    chat_sessions = ChatSession.objects.filter(user=user).order_by('-start_time')

    if session_id:
        try:
            active_session = ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            return redirect('chat') # Redirect if session doesn't exist or belong to user
    else:
        # Get the most recent session, or create a new one if none exist
        active_session = chat_sessions.first()
        if not active_session:
            active_session = ChatSession.objects.create(user=user)

    messages = active_session.messages.all().order_by('timestamp')

    if request.method == 'POST':
        user_message = request.POST.get('message')
        session_id_from_post = request.POST.get('session_id')
        
        try:
            session = ChatSession.objects.get(id=session_id_from_post, user=user)

            # Save user message
            ChatMessage.objects.create(session=session, is_user=True, message_text=user_message)

            # Get and save bot response from your AI adapter
            try:
                bot_response = chatbot.get_response(user_message)
                ChatMessage.objects.create(session=session, is_user=False, message_text=str(bot_response))
                
                return JsonResponse({'message': user_message, 'response': str(bot_response)})
            except Exception as e:
                error_message = f"Error processing message: {str(e)}"
                print(error_message)
                print(traceback.format_exc())
                
                # Save the error message as a bot response
                ChatMessage.objects.create(
                    session=session, 
                    is_user=False, 
                    message_text="I'm having trouble processing your request right now. Please try again later."
                )
                
                return JsonResponse({
                    'message': user_message, 
                    'response': "I'm having trouble processing your request right now. Please try again later."
                })
        except ChatSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)

    context = {
        'chat_sessions': chat_sessions,
        'active_session': active_session,
        'messages': messages
    }
    return render(request, 'chatbot/chat.html', context)

@login_required
def new_chat_session(request):
    # Create a new session and redirect to the chat view, which will load it
    new_session = ChatSession.objects.create(user=request.user)
    return redirect('chat_session', session_id=new_session.id)