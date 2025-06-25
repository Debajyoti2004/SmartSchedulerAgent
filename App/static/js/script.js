document.addEventListener('DOMContentLoaded', () => {
    const messageForm = document.getElementById('message-form');
    const userInput = document.getElementById('user-input');
    const messageList = document.getElementById('message-list');
    const sendButton = document.getElementById('send-button');
    const voiceToggle = document.getElementById('voice-toggle');

    let currentSessionId = null;
    let isVoiceMode = false;
    let thoughtBuffer = [];
    const socket = io();

    const createMessageElement = (role, content) => {
        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper ${role}`;
        const icon = document.createElement('span');
        icon.className = 'message-icon';
        icon.textContent = role === 'user' ? '👤' : '🤖';
        const bubbleContainer = document.createElement('div');
        bubbleContainer.className = 'message-bubble-container';
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = content;
        if (content === '...') {
            bubble.classList.add('typing-indicator');
        }
        bubbleContainer.appendChild(bubble);
        const timestamp = document.createElement('span');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
        bubbleContainer.appendChild(timestamp);
        const contentWrapper = document.createElement('div');
        contentWrapper.className = 'message-content';
        if (role === 'user') {
            contentWrapper.appendChild(bubbleContainer);
            contentWrapper.appendChild(icon);
        } else {
            contentWrapper.appendChild(icon);
            contentWrapper.appendChild(bubbleContainer);
        }
        wrapper.appendChild(contentWrapper);
        messageList.appendChild(wrapper);
        messageList.scrollTop = messageList.scrollHeight;
        return wrapper;
    };

    const appendThoughts = (assistantWrapper, thoughts) => {
        if (!thoughts || thoughts.length === 0) return;
        const bubbleContainer = assistantWrapper.querySelector('.message-bubble-container');
        if (!bubbleContainer) return;
        const thoughtsButton = document.createElement('button');
        thoughtsButton.className = 'thoughts-button';
        thoughtsButton.textContent = 'Show thoughts 🤔';
        const thoughtsContainer = document.createElement('div');
        thoughtsContainer.className = 'thoughts-container';
        thoughtsContainer.textContent = thoughts.join('\n\n');
        bubbleContainer.appendChild(thoughtsButton);
        bubbleContainer.appendChild(thoughtsContainer);
        thoughtsButton.addEventListener('click', () => {
            thoughtsContainer.classList.toggle('expanded');
            thoughtsButton.textContent = thoughtsContainer.classList.contains('expanded') 
                ? 'Hide thoughts' 
                : 'Show thoughts 🤔';
        });
    };

    const updateUIForVoiceMode = (active) => {
        isVoiceMode = active;
        userInput.disabled = active;
        sendButton.disabled = active;
        if (active) {
            userInput.placeholder = "Listening for your command...";
            userInput.classList.add('voice-active');
        } else {
            userInput.placeholder = "Type your message...";
            userInput.classList.remove('voice-active');
        }
    };

    socket.on('user_transcript', (data) => {
        createMessageElement('user', data.transcript);
        createMessageElement('assistant', '...');
    });
    
    socket.on('agent_thoughts', (data) => {
        thoughtBuffer = data.thoughts;
    });

    socket.on('agent_response', (data) => {
        const typingIndicator = messageList.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.closest('.message-wrapper.assistant').remove();
        }
        const assistantWrapper = createMessageElement('assistant', data.response);
        appendThoughts(assistantWrapper, thoughtBuffer);
        thoughtBuffer = [];
    });

    socket.on('voice_status', (data) => {
        updateUIForVoiceMode(data.status === 'started');
    });

    voiceToggle.addEventListener('change', () => {
        if (voiceToggle.checked) {
            window.speechSynthesis.cancel();
            socket.emit('start_voice');
        } else {
            socket.emit('stop_voice');
        }
    });

    messageForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (isVoiceMode) return;
        const text = userInput.value;
        if (!text.trim()) return;
        createMessageElement('user', text);
        userInput.value = '';
        sendButton.disabled = true;
        const typingIndicatorWrapper = createMessageElement('assistant', '...');
        try {
            const payload = { user_input: text, session_id: currentSessionId };
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            typingIndicatorWrapper.remove();
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            currentSessionId = data.session_id;
            const assistantWrapper = createMessageElement('assistant', data.final_response);
            appendThoughts(assistantWrapper, data.thoughts);
        } catch (error) {
            typingIndicatorWrapper.remove();
            createMessageElement('assistant', 'Sorry, I am having trouble connecting to my brain right now.');
        } finally {
            sendButton.disabled = false;
            userInput.focus();
        }
    });

    const initialGreeting = 'Hello! I am your smart scheduling assistant. Toggle "Voice Mode" on or type to get started.';
    createMessageElement('assistant', initialGreeting);
});