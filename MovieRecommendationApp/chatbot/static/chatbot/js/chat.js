$(document).ready(function() {
    // Scroll to the bottom of the chat box on page load
    scrollToBottom();

    // Handle form submission
    $('#chat-form').on('submit', function(e) {
        e.preventDefault();
        
        const userInput = $('#user-input').val().trim();
        if (!userInput) return; // Don't send empty messages
        
        const sessionId = $('input[name="session_id"]').val();
        
        // Clear the input field
        $('#user-input').val('');
        
        // Add user message to the chat box immediately
        addMessage(userInput, true);
        
        // Scroll to the bottom
        scrollToBottom();
        
        // Send the message to the server
        $.ajax({
            type: 'POST',
            url: window.location.pathname,
            data: {
                'message': userInput,
                'session_id': sessionId,
                'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function(data) {
                // Add bot response to the chat box
                addMessage(data.response, false);
                
                // Scroll to the bottom
                scrollToBottom();
            },
            error: function(xhr, status, error) {
                console.error('Error sending message:', error);
                addMessage('Sorry, there was an error processing your request.', false);
                scrollToBottom();
            }
        });
    });
    
    // Function to add a message to the chat box
    function addMessage(text, isUser) {
        const messageHtml = isUser ?
            `<div class="chat-message user-message">
                <div class="message-content">${text}</div>
                <div class="avatar user-avatar"><i class="fa fa-user"></i></div>
            </div>` :
            `<div class="chat-message bot-message">
                <div class="avatar bot-avatar"><i class="fa fa-android"></i></div>
                <div class="message-content">${text}</div>
            </div>`;
        
        $('#chat-box').append(messageHtml);
    }
    
    // Function to scroll to the bottom of the chat box
    function scrollToBottom() {
        const chatBox = document.getElementById('chat-box');
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});
