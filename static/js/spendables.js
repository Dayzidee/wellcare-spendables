/**
 * Well Care Spendables - Core Application JavaScript
 * Version: 2.0
 *
 * This file handles all core frontend interactions using a modern, modular approach.
 * Each feature is initialized by a dedicated function for clarity and maintainability.
 */

// Main application namespace to avoid polluting the global scope
const App = {
  /**
   * Initializes all core JavaScript functionality on page load.
   */
  init() {
    console.log("🌱 Well Care Spendables Initialized");

    this.mobileNavigation();
    this.sidePanels();
    this.alertDismissal();
    this.scrollAnimations();
    this.formValidation();
    this.copyToClipboard();
    this.notificationHandler();
    this.virtualCard();
    this.liveChat();

    // Any other initializers can be added here
  },

  /**
   * Handles the mobile navigation menu (hamburger) from scratch.
   * Toggles 'is-active' classes for a professional slide-in panel.
   */
  mobileNavigation() {
    const trigger = document.getElementById("mobile-menu-trigger");
    // IMPORTANT: The element that slides in is the .nav-links container.
    const panel = document.querySelector(".nav-links");
    const overlay = document.querySelector(".panel-overlay");

    if (!trigger || !panel || !overlay) {
      console.error("Mobile navigation elements not found.");
      return;
    }

    const closeMenu = () => {
        panel.classList.remove("is-active");
        trigger.classList.remove("is-active");
        overlay.classList.remove("is-active");
        trigger.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "";
    };

    const openMenu = () => {
        panel.classList.add("is-active");
        trigger.classList.add("is-active");
        overlay.classList.add("is-active");
        trigger.setAttribute("aria-expanded", "true");
        document.body.style.overflow = "hidden";
    };

    trigger.addEventListener("click", () => {
      if (panel.classList.contains("is-active")) {
        closeMenu();
      } else {
        openMenu();
      }
    });

    // Close conditions
    overlay.addEventListener("click", closeMenu);
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && panel.classList.contains("is-active")) {
        closeMenu();
      }
    });
  },

  /**
   * This function is being rebuilt from scratch.
   * The old implementation is removed.
   */
  liveChat() {
    const container = document.getElementById("chat-widget-container");
    if (!container) return;

    const toggleBtn = document.getElementById("chat-widget-toggle");
    const chatWindow = document.getElementById("chat-window");
    const closeBtn = document.getElementById("chat-close-btn");
    const messagesContainer = document.getElementById("chat-messages");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("chat-send-btn");

    const socket = io();

    const addMessage = (message, sender, timestamp) => {
      const msgDiv = document.createElement("div");
      msgDiv.classList.add("chat-message", `is-${sender}`);

      const msgSpan = document.createElement("span");
      msgSpan.textContent = message;
      msgDiv.appendChild(msgSpan);

      const timeSpan = document.createElement("span");
      timeSpan.classList.add("timestamp");
      timeSpan.textContent = timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      msgDiv.appendChild(timeSpan);

      messagesContainer.appendChild(msgDiv);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };

    const sendMessage = () => {
      const message = chatInput.value.trim();
      if (message) {
        socket.emit("send_message", { message: message });
        addMessage(message, "user");
        chatInput.value = "";
      }
    };

    const toggleChatWindow = (isOpen) => {
      const currentlyOpen = chatWindow.classList.contains("is-open");
      if (isOpen === currentlyOpen) return;

      if (isOpen) {
        chatWindow.classList.add("is-open");
        toggleBtn.classList.add("is-active");
        socket.emit("request_history");
      } else {
        chatWindow.classList.remove("is-open");
        toggleBtn.classList.remove("is-active");
      }
    };

    toggleBtn.addEventListener("click", () => toggleChatWindow(!chatWindow.classList.contains("is-open")));
    closeBtn.addEventListener("click", () => toggleChatWindow(false));

    sendBtn.addEventListener("click", sendMessage);
    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        sendMessage();
      }
    });

    socket.on("connect", () => console.log("💬 Customer connected to chat server."));

    socket.on('receive_message', (data) => {
        if (data.sender_type === 'agent') {
            addMessage(data.message, 'agent', data.timestamp);
        }
    });

    socket.on('chat_history', (data) => {
        messagesContainer.innerHTML = '<div class="chat-message is-system"><span>Welcome! An agent will be with you shortly.</span></div>';
        data.history.forEach(msg => {
            addMessage(msg.message_text, msg.sender_type, msg.timestamp);
        });
    });
  },

  /**
   * Handles virtual card display and interactions
   */
  virtualCard() {
    const flipper = document.querySelector(".virtual-card-flipper");
    const flipBtns = document.querySelectorAll(".card-flip-btn");
    const showDetailsCheckbox = document.getElementById(
      "show-details-checkbox"
    );
    const cardNumber = document.getElementById("card-number");
    const cardCvv = document.getElementById("card-cvv");

    if (!flipper || !showDetailsCheckbox || !cardNumber || !cardCvv) return;

    // Flip functionality
    flipBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        flipper.classList.toggle("is-flipped");
      });
    });

    // Show/hide details functionality
    showDetailsCheckbox.addEventListener("change", () => {
      const isChecked = showDetailsCheckbox.checked;
      cardNumber.classList.toggle("is-masked", !isChecked);
      cardCvv.classList.toggle("is-masked", !isChecked);
    });
  },

  /**
   * Manages all side panels (Settings, Notifications, Support).
   * Uses event delegation for efficiency.
   */
  sidePanels() {
    const overlay = document.querySelector(".panel-overlay");
    if (!overlay) return;

    const closeAllPanels = () => {
      document
        .querySelectorAll(".app-panel.is-active")
        .forEach((panel) => panel.classList.remove("is-active"));
      overlay.classList.remove("is-active");
      document.body.style.overflow = "";
    };

    document.body.addEventListener("click", (e) => {
      // Open panel trigger
      const trigger = e.target.closest('[id$="-panel-trigger"]');
      if (trigger) {
        const panelId = trigger.id.replace("-trigger", "");
        const panel = document.getElementById(panelId);
        if (panel) {
          closeAllPanels(); // Close others first
          panel.classList.add("is-active");
          overlay.classList.add("is-active");
          document.body.style.overflow = "hidden";
        }
      }

      // Close button or overlay
      if (e.target.closest(".close-panel-btn") || e.target === overlay) {
        closeAllPanels();
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeAllPanels();
    });
  },

  /**
   * Allows users to dismiss flash messages (alerts) with a smooth animation.
   */
  alertDismissal() {
    document.body.addEventListener("click", (e) => {
      const alert = e.target.closest(".alert");
      if (alert) {
        alert.classList.add("is-dismissing");
        // Remove the element after the animation completes
        alert.addEventListener("transitionend", () => alert.remove(), {
          once: true,
        });
      }
    });
  },

  /**
   * Initializes the Intersection Observer for on-scroll animations.
   * Looks for elements with .anim-* classes.
   */
  scrollAnimations() {
    const animatedElements = document.querySelectorAll(
      ".anim-fade-in-up, .anim-fade-in"
    );
    if (animatedElements.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const delay = parseInt(entry.target.dataset.delay) || 0;
            setTimeout(() => {
              entry.target.classList.add("is-visible");
            }, delay);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1 }
    );

    animatedElements.forEach((el) => observer.observe(el));
  },

  /**
   * Enhances form validation with real-time feedback for specific input types.
   */
  formValidation() {
    const currencyInputs = document.querySelectorAll(
      'input[type="number"][step="0.01"]'
    );
    currencyInputs.forEach((input) => {
      input.addEventListener("input", (e) => {
        // Simple regex to allow numbers and one decimal point
        e.target.value = e.target.value
          .replace(/[^0-9.]/g, "")
          .replace(/(\..*)\./g, "$1");
      });
    });
  },

  /**
   * Handles the "Copy to Clipboard" functionality for account numbers.
   */
  copyToClipboard() {
    const copyBtn = document.getElementById("copy-identifier-btn");
    if (!copyBtn) return;

    const rawAccountNumber = document.getElementById("raw-account-number");
    if (!rawAccountNumber) return;

    copyBtn.addEventListener("click", () => {
      navigator.clipboard
        .writeText(rawAccountNumber.textContent.trim())
        .then(() => {
          const originalContent = copyBtn.innerHTML;
          copyBtn.innerHTML = `<i class="fas fa-check"></i> Copied!`;
          copyBtn.classList.add("btn-accent");
          copyBtn.disabled = true;
          setTimeout(() => {
            copyBtn.innerHTML = originalContent;
            copyBtn.classList.remove("btn-accent");
            copyBtn.disabled = false;
          }, 2000);
        })
        .catch((err) => {
          console.error("Failed to copy text: ", err);
        });
    });
  },

  /**
   * Handles marking notifications as read when the panel is opened.
   */
  notificationHandler() {
    const trigger = document.getElementById("notifications-panel-trigger");
    if (!trigger) return;

    trigger.addEventListener("click", () => {
      const dot = trigger.querySelector(".notification-dot");
      if (dot) {
        // Optimistically remove the dot from the UI
        dot.style.display = "none";

        // Call the API in the background to mark as read
        const csrfToken = document.querySelector(
          'input[name="csrf_token"]'
        )?.value;
        fetch("/api/notifications/mark-as-read", {
          method: "POST",
          headers: { "X-CSRFToken": csrfToken },
        }).catch((err) => {
          console.error("Failed to mark notifications as read:", err);
          // If it fails, maybe show the dot again? For now, we just log.
        });
      }
    });
  },
};

// Start the application once the DOM is ready
document.addEventListener("DOMContentLoaded", () => App.init());
