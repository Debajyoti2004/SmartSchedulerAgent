document.addEventListener('DOMContentLoaded', () => {
    const messageForm = document.getElementById('message-form');
    const userInput = document.getElementById('user-input');
    const messageList = document.getElementById('message-list');
    const sendButton = document.getElementById('send-button');
    const micButton = document.getElementById('mic-button');

    let currentSessionId = null;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.lang = 'en-US';

        recognition.onresult = (event) => {
            const transcript = event.results[event.results.length - 1][0].transcript;
            userInput.value = transcript;
            messageForm.requestSubmit(sendButton);
        };

        recognition.onstart = () => micButton.classList.add('is-listening');
        recognition.onend = () => micButton.classList.remove('is-listening');
        recognition.onerror = (event) => {
            console.error("Speech recognition error", event.error);
            micButton.classList.remove('is-listening');
        };
    } else {
        micButton.style.display = 'none';
    }

    micButton.addEventListener('click', () => {
        if (recognition && !micButton.classList.contains('is-listening')) {
            try {
                recognition.start();
            } catch (e) { console.error("Mic already active or error starting:", e); }
        }
    });

    const speak = (text) => {
        if (!window.speechSynthesis) return;
        speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        speechSynthesis.speak(utterance);
    };

    const createMessageElement = (role, content) => {
        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper ${role}`;

        const icon = document.createElement('span');
        icon.className = 'message-icon';
        icon.textContent = role === 'user' ? '👤' : '🤖';

        const bubbleContainer = document.createElement('div');
        bubbleContainer.className = 'message-bubble-container';

        const bubble = document.createElement('div');
        bubble.className = `message-bubble`;
        
        const p = document.createElement('p');
        p.textContent = content;
        if(content === '...'){
             p.classList.add('typing-indicator');
        }
        bubble.appendChild(p);
        
        bubbleContainer.appendChild(bubble);

        const timestamp = document.createElement('span');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
        bubbleContainer.appendChild(timestamp);

        if (role === 'user') {
            wrapper.appendChild(bubbleContainer);
            wrapper.appendChild(icon);
        } else {
            wrapper.appendChild(icon);
            wrapper.appendChild(bubbleContainer);
        }
        
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

    const submitUserInput = async (text) => {
        if (!text.trim()) return;

        createMessageElement('user', text);
        userInput.value = '';
        sendButton.disabled = true;
        micButton.disabled = true;
        
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
            speak(data.final_response);

        } catch (error) {
            console.error('Error:', error);
            typingIndicatorWrapper.remove();
            const errorMsg = 'Sorry, I am having trouble connecting to my brain right now.';
            createMessageElement('assistant', errorMsg);
            speak(errorMsg);
        } finally {
            sendButton.disabled = false;
            micButton.disabled = false;
            userInput.focus();
        }
    };

    messageForm.addEventListener('submit', (e) => {
        e.preventDefault();
        submitUserInput(userInput.value);
    });

    const initialGreeting = 'Hello! I am your smart scheduling assistant. How can I help you?';
    createMessageElement('assistant', initialGreeting);
    speak(initialGreeting);
});