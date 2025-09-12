document.addEventListener("DOMContentLoaded", () => {
    const AdminChat = {
        // State
        socket: null,
        activeSessionId: null,
        activeCustomerId: null,

        // DOM Elements
        sessionList: document.getElementById("session-list"),
        welcomeScreen: document.getElementById("chat-welcome-screen"),
        activeScreen: document.getElementById("chat-active-screen"),
        messagesContainer: document.getElementById("chat-messages"),
        customerNameEl: document.getElementById("chat-active-customer-name"),
        chatInput: document.getElementById("admin-chat-input"),
        sendBtn: document.getElementById("admin-chat-send-btn"),
        sidebarToggle: document.getElementById("sidebar-toggle"),
        chatPageLayout: document.querySelector(".chat-page-layout"),
        sidebarOverlay: document.querySelector(".sidebar-overlay"),

        init() {
            if (!this.chatPageLayout) return; // Don't run if not on the chat page
            this.connectSocket();
            this.bindEvents();

            const preselectedSessionId = document.body.dataset.preselectedSessionId;
            if (preselectedSessionId) {
                const targetSessionEl = this.sessionList.querySelector(
                    `.list-item[data-session-id="${preselectedSessionId}"]`
                );
                if (targetSessionEl) {
                    this.loadSession(targetSessionEl);
                }
            }
        },

        connectSocket() {
            this.socket = io();

            this.socket.on("connect", () => console.log("💬 Admin connected to chat server."));

            this.socket.on("chat_history", (data) => {
                this.renderChatHistory(data.history);
            });

            this.socket.on("receive_message", (data) => {
                if (data.session_id == this.activeSessionId) {
                    this.addMessage(data.message, data.sender_type, data.timestamp);
                } else {
                    this.showNotificationDot(data.session_id);
                }
            });
        },

        bindEvents() {
            this.sessionList.addEventListener("click", (e) => {
                const sessionItem = e.target.closest(".list-item");
                if (sessionItem) {
                    e.preventDefault();
                    this.loadSession(sessionItem);
                }
            });

            this.sendBtn.addEventListener("click", () => this.sendMessage());
            this.chatInput.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            this.sidebarToggle.addEventListener("click", () => {
                this.chatPageLayout.classList.toggle("is-sidebar-open");
            });

            this.sidebarOverlay.addEventListener("click", () => {
                this.chatPageLayout.classList.remove("is-sidebar-open");
            });
        },

        loadSession(sessionElement) {
            this.sessionList.querySelectorAll(".list-item.is-active").forEach(item => item.classList.remove("is-active"));
            sessionElement.classList.add("is-active");

            this.activeSessionId = sessionElement.dataset.sessionId;
            this.activeCustomerId = sessionElement.dataset.customerId;

            this.hideNotificationDot(this.activeSessionId);

            this.welcomeScreen.classList.add("is-hidden");
            this.activeScreen.classList.remove("is-hidden");
            this.customerNameEl.textContent = sessionElement.querySelector(".list-item-title").textContent;

            this.socket.emit("request_history", { session_id: this.activeSessionId });
        },

        renderChatHistory(history) {
            // Clear existing messages more safely
            while (this.messagesContainer.firstChild) {
                this.messagesContainer.removeChild(this.messagesContainer.firstChild);
            }

            if (history.length === 0) {
                const systemMsg = document.createElement('div');
                systemMsg.classList.add('chat-message', 'is-system');
                systemMsg.innerHTML = '<span>No messages in this session yet.</span>';
                this.messagesContainer.appendChild(systemMsg);
            } else {
                history.forEach(msg => {
                    // Note: addMessage is already safe as it appends
                    this.addMessage(msg.message_text, msg.sender_type, msg.timestamp);
                });
            }
        },

        addMessage(message, sender, timestamp) {
            const msgDiv = document.createElement("div");
            msgDiv.classList.add("chat-message", `is-${sender}`);

            const msgSpan = document.createElement("span");
            msgSpan.textContent = message;
            msgDiv.appendChild(msgSpan);

            const timeSpan = document.createElement("span");
            timeSpan.classList.add("timestamp");
            timeSpan.textContent = timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            msgDiv.appendChild(timeSpan);

            this.messagesContainer.appendChild(msgDiv);
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        },

        sendMessage() {
            const message = this.chatInput.value.trim();
            if (message && this.activeCustomerId) {
                this.socket.emit("agent_send_message", {
                    message: message,
                    customer_id: this.activeCustomerId,
                });
                this.addMessage(message, "agent");
                this.chatInput.value = "";
            }
        },

        showNotificationDot(sessionId) {
            const sessionItem = this.sessionList.querySelector(`.list-item[data-session-id="${sessionId}"]`);
            if (sessionItem) {
                sessionItem.querySelector(".notification-dot").classList.remove("is-hidden");
            }
        },

        hideNotificationDot(sessionId) {
            const sessionItem = this.sessionList.querySelector(`.list-item[data-session-id="${sessionId}"]`);
            if (sessionItem) {
                sessionItem.querySelector(".notification-dot").classList.add("is-hidden");
            }
        }
    };

    AdminChat.init();
});
