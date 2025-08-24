document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');

    // Function to add a message to the chat box
    const addMessage = (text, sender) => {
        const message = document.createElement('div');
        message.classList.add('message', `${sender}-message`);
        message.innerText = text;
        chatBox.appendChild(message);
        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the latest message
    };

    // Function to handle sending a message
    const sendMessage = async () => {
        const text = userInput.value.trim();
        if (text === "") return;

        addMessage(text, 'user');
        userInput.value = '';

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });
            const data = await response.json();
            addMessage(data.reply, 'bot');
        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, something went wrong. Please try again.', 'bot');
        }
    };

    // Event listeners
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Start the conversation on page load
    const startConversation = async () => {
        try {
            const response = await fetch('/start', { method: 'POST' });
            const data = await response.json();
            addMessage(data.reply, 'bot');
        } catch (error) {
            console.error('Error starting conversation:', error);
            addMessage('Welcome! I seem to be having trouble starting. Please refresh.', 'bot');
        }
    };

    startConversation();
});