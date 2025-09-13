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
        chatInput: document.getElementById("chat-input"),
        sendBtn: document.getElementById("chat-send-btn"),
        sidebarToggle: document.getElementById("sidebar-toggle"),
        chatPageLayout: document.querySelector(".chat-page-layout"),
        sidebarOverlay: document.querySelector(".sidebar-overlay"),
        userDetailsToggle: document.getElementById("user-details-toggle"),
        userDetailsPanel: document.getElementById("user-details-panel"),
        userDetailsCloseBtn: document.getElementById("user-details-close-btn"),

        init() {
            if (!this.chatPageLayout) return;
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

            if (this.sidebarToggle) {
                this.sidebarToggle.addEventListener("click", () => {
                    this.chatPageLayout.classList.toggle("is-sidebar-open");
                });
            }

            if (this.sidebarOverlay) {
                this.sidebarOverlay.addEventListener("click", () => {
                    this.chatPageLayout.classList.remove("is-sidebar-open");
                });
            }

            if (this.userDetailsToggle) {
                this.userDetailsToggle.addEventListener("click", () => {
                    this.chatPageLayout.classList.add("is-user-details-open");
                });
            }

            if (this.userDetailsCloseBtn) {
                this.userDetailsCloseBtn.addEventListener("click", () => {
                    this.chatPageLayout.classList.remove("is-user-details-open");
                });
            }
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
            this.loadUserDetails(this.activeCustomerId);
        },

        loadUserDetails(customerId) {
            fetch(`/api/user_details/${customerId}`)
                .then(response => response.json())
                .then(data => {
                    const content = this.userDetailsPanel.querySelector('.panel-content');
                    content.innerHTML = `
                        <div><strong>Username:</strong> ${data.username}</div>
                        <div><strong>Email:</strong> ${data.email}</div>
                        <div><strong>Full Name:</strong> ${data.full_name}</div>
                        <div><strong>Phone:</strong> ${data.phone_number}</div>
                        <div><strong>Tier:</strong> ${data.account_tier}</div>
                        <div><strong>Joined:</strong> ${data.date_joined}</div>
                    `;
                });
        },

        renderChatHistory(history) {
            this.messagesContainer.innerHTML = "";
            if (history.length === 0) {
                this.messagesContainer.innerHTML = '<div class="chat-message is-system"><span>No messages in this session yet.</span></div>';
            } else {
                history.forEach(msg => {
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
