document.addEventListener('DOMContentLoaded', () => {
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotContainer = document.getElementById('chatbot-container');
    const chatbotClose = document.getElementById('chatbot-close');
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');
    const chatBox = document.getElementById('chat-box');

    const AI_API_URL = "https://demetasgaroglu-bookmind-ai.hf.space/api/chat";

    // Mesaj geçmişini sessionStorage'dan yükle
    let chatHistory = JSON.parse(sessionStorage.getItem('bookmind_chat_history')) || [
        { text: "Merhaba! Ben BookMind AI. Size nasıl yardımcı olabilirim?", sender: "bot" }
    ];

    // Geçmişi ekrana çiz
    const renderHistory = () => {
        chatBox.innerHTML = '';
        chatHistory.forEach(msg => {
            appendMessageToUI(msg.text, msg.sender);
        });
    };

    chatbotToggle.addEventListener('click', () => {
        chatbotContainer.classList.add('open');
        chatbotToggle.classList.add('hidden');
    });

    chatbotClose.addEventListener('click', () => {
        chatbotContainer.classList.remove('open');
        chatbotToggle.classList.remove('hidden');
    });

    const appendMessageToUI = (text, sender) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        msgDiv.textContent = text;
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    const addMessage = (text, sender) => {
        chatHistory.push({ text, sender });
        sessionStorage.setItem('bookmind_chat_history', JSON.stringify(chatHistory));
        appendMessageToUI(text, sender);
    };

    const showTyping = () => {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
        chatBox.appendChild(typingDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
        return typingDiv;
    };

    const handleSend = async () => {
        const text = chatInput.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        chatInput.value = '';

        const typing = showTyping();

        try {
            const userId = (typeof auth !== 'undefined' && auth.currentUser) 
                           ? auth.currentUser.uid 
                           : "anonymous_user";

            const response = await fetch(AI_API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    message: text,
                    user_id: userId
                })
            });

            if (!response.ok) {
                throw new Error(`AI servisi hata döndürdü (Kod: ${response.status})`);
            }

            const data = await response.json();
            typing.remove();
            
            const aiReply = data.response || data.reply || data.message || "Yanıt alınamadı.";
            addMessage(aiReply, 'bot');

        } catch (error) {
            console.error("Chatbot Hatası:", error);
            typing.remove();
            addMessage(`Üzgünüm, şu an bağlantı kuramıyorum. (Hata: ${error.message})`, "bot");
        }
    };

    chatSend.addEventListener('click', handleSend);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });

    // Sayfa yüklendiğinde geçmişi göster
    renderHistory();
});
