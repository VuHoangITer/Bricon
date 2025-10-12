/**
 * Hoangvn Chatbot Widget
 * Tích hợp Gemini AI cho tư vấn khách hàng
 */

class ChatbotWidget {
    constructor() {
        this.isOpen = false;
        this.isTyping = false;
        this.remainingRequests = 20;

        // DOM elements
        this.chatButton = document.getElementById('chatbotButton');
        this.chatWidget = document.getElementById('chatbotWidget');
        this.closeBtn = document.getElementById('chatbotCloseBtn');
        this.messagesContainer = document.getElementById('chatbotMessages');
        this.userInput = document.getElementById('chatbotInput');
        this.sendBtn = document.getElementById('chatbotSendBtn');
        this.resetBtn = document.getElementById('chatbotResetBtn');
        this.requestCountEl = document.getElementById('requestCount');

        // Kiểm tra các elements có tồn tại
        if (!this.chatButton || !this.chatWidget) {
            console.error('Chatbot elements not found');
            return;
        }

        this.init();
    }

    init() {
        // Event listeners
        this.chatButton.addEventListener('click', () => this.toggleChat());
        this.closeBtn.addEventListener('click', () => this.toggleChat());
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.resetBtn.addEventListener('click', () => this.resetChat());

        // Enter để gửi tin nhắn
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-focus input khi mở chat
        this.chatWidget.addEventListener('transitionend', () => {
            if (this.isOpen) {
                this.userInput.focus();
            }
        });

        console.log('Chatbot initialized successfully');
    }

    toggleChat() {
        this.isOpen = !this.isOpen;
        this.chatWidget.classList.toggle('active');

        if (this.isOpen) {
            this.userInput.focus();
            this.scrollToBottom();
        }
    }

    async sendMessage() {
        const message = this.userInput.value.trim();

        if (!message || this.isTyping) {
            return;
        }

        // Kiểm tra độ dài tin nhắn
        if (message.length > 500) {
            alert('Tin nhắn quá dài! Vui lòng nhập tối đa 500 ký tự.');
            return;
        }

        // Hiển thị tin nhắn người dùng
        this.addMessage(message, 'user');
        this.userInput.value = '';

        // Disable input khi đang gửi
        this.setInputState(false);

        // Hiển thị typing indicator
        this.showTyping();

        try {
            // Gửi request đến backend
            const response = await fetch('/chatbot/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();

            // Ẩn typing indicator
            this.hideTyping();

            if (response.ok) {
                // Hiển thị phản hồi từ bot
                this.addMessage(data.response, 'bot');

                // Cập nhật số request còn lại
                if (data.remaining_requests !== undefined) {
                    this.remainingRequests = data.remaining_requests;
                    this.updateRequestCount();
                }
            } else {
                // Hiển thị lỗi
                this.addMessage(
                    data.error || data.response || 'Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại! 😊',
                    'bot'
                );
            }

        } catch (error) {
            console.error('Chatbot error:', error);
            this.hideTyping();
            this.addMessage(
                'Xin lỗi, không thể kết nối đến server. Vui lòng kiểm tra kết nối mạng! 🔌',
                'bot'
            );
        } finally {
            // Enable lại input
            this.setInputState(true);
            this.userInput.focus();
        }
    }

    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${sender}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'chatbot-message-content';

        // Chuyển đổi line breaks thành <br>
        contentDiv.innerHTML = this.escapeHtml(text).replace(/\n/g, '<br>');

        messageDiv.appendChild(contentDiv);
        this.messagesContainer.appendChild(messageDiv);

        // Scroll to bottom
        this.scrollToBottom();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showTyping() {
        this.isTyping = true;

        const typingDiv = document.createElement('div');
        typingDiv.className = 'chatbot-message bot';
        typingDiv.id = 'chatbotTypingIndicator';

        const typingContent = document.createElement('div');
        typingContent.className = 'chatbot-typing';
        typingContent.innerHTML = '<span></span><span></span><span></span>';

        typingDiv.appendChild(typingContent);
        this.messagesContainer.appendChild(typingDiv);

        this.scrollToBottom();
    }

    hideTyping() {
        this.isTyping = false;
        const typingIndicator = document.getElementById('chatbotTypingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    setInputState(enabled) {
        this.userInput.disabled = !enabled;
        this.sendBtn.disabled = !enabled;

        if (enabled) {
            this.sendBtn.style.opacity = '1';
        } else {
            this.sendBtn.style.opacity = '0.5';
        }
    }

    scrollToBottom() {
        // Smooth scroll to bottom
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }

    async resetChat() {
        if (!confirm('Bạn có chắc muốn làm mới hội thoại? Tất cả tin nhắn sẽ bị xóa.')) {
            return;
        }

        try {
            const response = await fetch('/chatbot/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                // Xóa tất cả tin nhắn (trừ tin nhắn chào mừng)
                const messages = this.messagesContainer.querySelectorAll('.chatbot-message');
                messages.forEach((msg, index) => {
                    if (index > 0) { // Giữ lại tin nhắn đầu tiên
                        msg.remove();
                    }
                });

                // Reset counter
                this.remainingRequests = 20;
                this.updateRequestCount();

                // Thông báo thành công
                this.addMessage('Đã làm mới hội thoại! Tôi có thể giúp gì cho bạn? 😊', 'bot');
            }
        } catch (error) {
            console.error('Reset error:', error);
            alert('Không thể làm mới hội thoại. Vui lòng thử lại!');
        }
    }

    updateRequestCount() {
        if (this.requestCountEl) {
            this.requestCountEl.textContent = `Còn ${this.remainingRequests} tin nhắn`;
        }
    }
}

// Khởi tạo chatbot khi DOM loaded
document.addEventListener('DOMContentLoaded', () => {
    // Kiểm tra xem các elements có tồn tại không
    if (document.getElementById('chatbotButton')) {
        new ChatbotWidget();
    }
});