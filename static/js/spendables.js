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
    this.deactivatedDashboardHandler();

    // Any other initializers can be added here
  },

  deactivatedDashboardHandler() {
    const dashboard = document.querySelector('.deactivated-dashboard');
    if (!dashboard) return;

    const modal = document.getElementById('deactivated-modal');
    const closeBtn = document.getElementById('deactivated-modal-close');

    if (!modal || !closeBtn) return;

    dashboard.addEventListener('click', (e) => {
      // Check if the click is on a disabled element, but not the close button itself
      if (e.target.closest('button, a.btn, input, select, textarea, a.list-item') && !e.target.closest('#deactivated-modal-close')) {
        e.preventDefault();
        e.stopPropagation();
        modal.classList.add('is-visible');
      }
    }, true); // Use capture phase to catch event early

    closeBtn.addEventListener('click', () => {
      modal.classList.remove('is-visible');
    });
  },

  /**
   * Rebuilt from scratch to handle a traditional dropdown mobile menu.
   */
  mobileNavigation() {
    const trigger = document.getElementById("mobile-menu-trigger");
    const navLinks = document.querySelector(".nav-links");

    if (!trigger || !navLinks) {
      console.error("Mobile navigation elements not found for dropdown.");
      return;
    }

    trigger.addEventListener("click", function() {
      // The 'this' keyword refers to the trigger button
      this.classList.toggle("is-active");
      // The navLinks variable is the element we want to show/hide
      navLinks.classList.toggle("is-active");

      // Set ARIA attribute for accessibility
      const isExpanded = this.classList.contains("is-active");
      this.setAttribute("aria-expanded", isExpanded);
    });
  },

// Replace the liveChat() function in your spendables.js with this updated version

/**
 * User Chat Widget - Completely rebuilt with modern patterns
 */
liveChat() {
    const widgetContainer = document.getElementById('chat-widget-container');
    if (!widgetContainer) return;

    // Corrected IDs to match the HTML in dashboard.html
    const toggle = document.getElementById('chat-widget-toggle');
    const window = document.getElementById('chat-window');
    const closeBtn = document.getElementById('chat-close-btn');
    const messages = document.getElementById('chat-messages');
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send-btn');

    // The form element does not exist in the HTML, so we remove it.
    // We will add a direct click listener to the send button.
    if (!toggle || !window || !closeBtn || !messages || !input || !sendBtn) {
        console.error('One or more chat widget elements are missing from the DOM.');
        return;
    }

    // Initialize socket connection
    let socket = null;
    let isConnected = false;
    let isOpen = false;

    try {
        socket = io();

        socket.on('connect', () => {
            console.log('💬 Customer connected to chat server');
            isConnected = true;
            updateSendButtonState();
        });

        socket.on('disconnect', () => {
            console.log('💬 Disconnected from chat server');
            isConnected = false;
            updateSendButtonState();
            addSystemMessage('Connection lost. Trying to reconnect...');
        });

        socket.on('receive_message', (data) => {
            if (data.sender_type === 'agent') {
                addMessage(data.message, 'agent', data.timestamp);
            }
        });

        let historyLoaded = false; // <-- ADD THIS FLAG

        socket.on('chat_history', (data) => {
            if (!historyLoaded) {
                data.history.forEach(msg => {
                    addMessage(msg.message_text, msg.sender_type, msg.timestamp);
                });
                historyLoaded = true;
            }
        });

    } catch (error) {
        console.error('Socket initialization failed:', error);
        isConnected = false;
        updateSendButtonState();
    }

    // Event Listeners
    toggle.addEventListener('click', () => toggleChat());
    closeBtn.addEventListener('click', () => closeChat());

    sendBtn.addEventListener('click', sendMessage);

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 100) + 'px';
    });

    // Close on escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && isOpen) {
            closeChat();
        }
    });

    // Functions
    function toggleChat() {
        if (isOpen) {
            closeChat();
        } else {
            openChat();
        }
    }

    function openChat() {
        isOpen = true;
        toggle.classList.add('active');
        window.classList.add('active');

        // Reset UI and state every time chat is opened for robustness
        // messages.innerHTML = ''; // This was the source of the bug, clearing the chat unexpectedly.
        addSystemMessage("Welcome! An agent will be with you shortly.");
        historyLoaded = false;

        // Focus input after animation
        setTimeout(() => {
            input.focus();
        }, 300);

        // Request chat history
        if (socket && isConnected) {
            socket.emit('request_history');
        }
    }

    function closeChat() {
        isOpen = false;
        toggle.classList.remove('active');
        window.classList.remove('active');
    }

    function sendMessage() {
        const message = input.value.trim();
        if (!message || !isConnected) return;

        // Add message to UI immediately
        addMessage(message, 'user');

        // Send to server
        socket.emit('send_message', { message: message });

        // Clear input
        input.value = '';
        input.style.height = 'auto';
        input.focus();
    }

    function addMessage(content, type, timestamp = null) {
        const message = document.createElement('div');
        message.className = `message ${type}`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;

        const messageTime = document.createElement('div');
        messageTime.className = 'message-timestamp';
        messageTime.textContent = timestamp || formatTimestamp(new Date());

        message.appendChild(messageContent);
        message.appendChild(messageTime);

        messages.appendChild(message);
        scrollToBottom();
    }

    function addSystemMessage(content) {
        addMessage(content, 'system');
    }

    function scrollToBottom() {
        requestAnimationFrame(() => {
            messages.scrollTop = messages.scrollHeight;
        });
    }

    function formatTimestamp(date) {
        return date.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    function updateSendButtonState() {
        sendBtn.disabled = !isConnected;
    }
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

// Call the deactivation handler separately to ensure it runs
App.deactivatedDashboardHandler();
