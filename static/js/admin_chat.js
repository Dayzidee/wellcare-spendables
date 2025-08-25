/**
 * Well Care Spendables - Admin Chat Interface JavaScript
 * Version: 1.0
 */
const preselectedCustomerId = document.body.dataset.preselectedCustomerId;
const preselectedSessionId = document.body.dataset.preselectedSessionId;
document.addEventListener("DOMContentLoaded", () => {
  const AdminChat = {
    // DOM Elements
    sessionList: document.getElementById("session-list"),
    conversationArea: document.getElementById("chat-conversation-area"),
    welcomeScreen: document.getElementById("chat-welcome-screen"),
    activeScreen: document.getElementById("chat-active-screen"),
    messagesContainer: document.getElementById("chat-messages"),
    customerNameEl: document.getElementById("chat-active-customer-name"),
    chatInput: document.getElementById("chat-input"),
    sendBtn: document.getElementById("chat-send-btn"),

    // State
    socket: null,
    activeSessionId: null,
    activeCustomerId: null,

    init() {
      this.connectSocket();
      this.bindEvents();

      // --- NEW: AUTO-LOAD CHAT ON PAGE LOAD ---
      if (preselectedSessionId && preselectedCustomerId) {
        const targetSessionEl = this.sessionList.querySelector(
          `.list-item[data-session-id="${preselectedSessionId}"]`
        );
        // If the session is already in the list, load it
        if (targetSessionEl) {
          this.loadSession(
            preselectedSessionId,
            preselectedCustomerId,
            targetSessionEl
          );
        } else {
          // If the user has never chatted, the session might not exist in the "open" list yet.
          // We can't fully load it, but we can show a placeholder.
          this.showPlaceholderForNewChat(preselectedCustomerId);
        }
      }
    },

    connectSocket() {
      this.socket = io();

      this.socket.on("connect", () => {
        console.log("💬 Admin connected to chat server");
        // Tell the server this is an admin/agent
        this.socket.emit("agent_join_admin_channel");
      });

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

      this.socket.on("new_customer_session", (data) => {
        this.addSessionToList(data);
      });
    },

    bindEvents() {
      this.sessionList.addEventListener("click", (e) => {
        e.preventDefault();
        const sessionItem = e.target.closest(".list-item");
        if (sessionItem) {
          const sessionId = sessionItem.dataset.sessionId;
          const customerId = sessionItem.dataset.customerId;
          this.loadSession(sessionId, customerId, sessionItem);
        }
      });

      this.sendBtn.addEventListener("click", () => this.sendMessage());
      this.chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") this.sendMessage();
      });
    },

    loadSession(sessionId, customerId, sessionElement) {
      // Update active state in the UI
      this.sessionList
        .querySelectorAll(".list-item")
        .forEach((item) => item.classList.remove("is-active"));
      sessionElement.classList.add("is-active");
      this.hideNotificationDot(sessionId);

      // Update internal state
      this.activeSessionId = sessionId;
      this.activeCustomerId = customerId;

      // Update UI
      this.welcomeScreen.classList.add("is-hidden");
      this.activeScreen.classList.remove("is-hidden");
      this.customerNameEl.textContent = `Chat with ${
        sessionElement.querySelector(".list-item-title").textContent
      }`;

      // Request chat history for this session from the server
      this.socket.emit("agent_request_history", { session_id: sessionId });
    },

    // --- NEW HELPER FUNCTION ---
    showPlaceholderForNewChat(customerId) {
      // This is for when an agent clicks "Chat" on a user who has never chatted before.
      this.welcomeScreen.classList.add("is-hidden");
      this.activeScreen.classList.remove("is-hidden");
      // We need the customer's name. We can't get it easily here without an API call.
      // A simple solution is to just show the ID.
      this.customerNameEl.textContent = `New Chat with Customer #${customerId}`;
      this.messagesContainer.innerHTML =
        '<p class="empty-state">This user has no chat history. Send a message to begin.</p>';

      // Set the active state so the agent can start typing
      this.activeSessionId = null; // No session ID yet
      this.activeCustomerId = customerId;
    },

    renderChatHistory(history) {
      this.messagesContainer.innerHTML = "";
      history.forEach((msg) => {
        this.addMessage(msg.message_text, msg.sender_type, msg.timestamp);
      });
    },

    addMessage(message, sender, timestamp) {
      const msgDiv = document.createElement("div");
      msgDiv.classList.add("chat-message", `is-${sender}`);

      const msgSpan = document.createElement("span");
      msgSpan.textContent = message;

      const timeSpan = document.createElement("span");
      timeSpan.classList.add("timestamp");
      timeSpan.textContent =
        timestamp ||
        new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        });

      msgDiv.appendChild(msgSpan);
      msgDiv.appendChild(timeSpan);
      this.messagesContainer.appendChild(msgDiv);
      this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    },

    sendMessage() {
      const message = this.chatInput.value.trim();
      if (message && this.activeSessionId) {
        const data = {
          message: message,
          session_id: this.activeSessionId,
          customer_id: this.activeCustomerId, // The agent needs to tell the server who to send it to
        };
        this.socket.emit("agent_send_message", data);
        this.addMessage(message, "agent"); // Optimistically add agent's message
        this.chatInput.value = "";
      }
    },

    showNotificationDot(sessionId) {
      const sessionItem = this.sessionList.querySelector(
        `.list-item[data-session-id="${sessionId}"]`
      );
      if (sessionItem) {
        sessionItem
          .querySelector(".notification-dot")
          .classList.remove("is-hidden");
      }
    },

    hideNotificationDot(sessionId) {
      const sessionItem = this.sessionList.querySelector(
        `.list-item[data-session-id="${sessionId}"]`
      );
      if (sessionItem) {
        sessionItem
          .querySelector(".notification-dot")
          .classList.add("is-hidden");
      }
    },

    addSessionToList(sessionData) {
      // Simple way to avoid duplicates
      if (
        this.sessionList.querySelector(`[data-session-id="${sessionData.id}"]`)
      )
        return;

      const sessionLink = document.createElement("a");
      sessionLink.href = "#";
      sessionLink.className = "list-item";
      sessionLink.dataset.sessionId = sessionData.id;
      sessionLink.dataset.customerId = sessionData.customer_id;

      sessionLink.innerHTML = `
            <div class="list-item-content">
                <strong class="list-item-title">${sessionData.customer_name}</strong>
                <span class="list-item-subtitle">Status: ${sessionData.status}</span>
            </div>
            <span class="notification-dot"></span> <!-- Show dot for new session -->
        `;
      this.sessionList.prepend(sessionLink);
    },
  };

  AdminChat.init();
});
