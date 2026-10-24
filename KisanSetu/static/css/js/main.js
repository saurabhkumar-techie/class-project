
/* =========================================
   KisanSetu - Main JavaScript
   ========================================= */

document.addEventListener("DOMContentLoaded", function () {

    // 1. Automatically hide flash messages
    const alerts = document.querySelectorAll(
        ".alert:not(.alert-permanent)"
    );

    alerts.forEach(function (alert) {
        setTimeout(function () {
            if (document.body.contains(alert)) {
                alert.style.transition = "opacity 0.4s ease";
                alert.style.opacity = "0";

                setTimeout(function () {
                    alert.remove();
                }, 400);
            }
        }, 5000);
    });


    // 2. Confirmation before deleting an item
    const deleteButtons = document.querySelectorAll(
        "[data-confirm-delete]"
    );

    deleteButtons.forEach(function (button) {
        button.addEventListener("click", function (event) {
            const message =
                button.dataset.confirmDelete ||
                "Are you sure you want to delete this item?";

            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });


    // 3. Show or hide password
    const passwordToggles = document.querySelectorAll(
        "[data-toggle-password]"
    );

    passwordToggles.forEach(function (toggle) {
        toggle.addEventListener("click", function () {
            const targetId = toggle.dataset.togglePassword;
            const passwordInput = document.getElementById(targetId);

            if (!passwordInput) {
                return;
            }

            if (passwordInput.type === "password") {
                passwordInput.type = "text";
                toggle.textContent = "Hide Password";
            } else {
                passwordInput.type = "password";
                toggle.textContent = "Show Password";
            }
        });
    });


    // 4. Basic form validation
    const forms = document.querySelectorAll(
        "form[data-validate]"
    );

    forms.forEach(function (form) {
        form.addEventListener("submit", function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }

            form.classList.add("was-validated");
        });
    });


    // 5. Automatically calculate order total
    const quantityInput = document.getElementById("order-quantity");
    const priceElement = document.getElementById("crop-price");
    const totalElement = document.getElementById("order-total");

    if (quantityInput && priceElement && totalElement) {
        const price = parseFloat(priceElement.dataset.price);

        function updateOrderTotal() {
            const quantity = parseFloat(quantityInput.value);

            if (
                Number.isFinite(price) &&
                Number.isFinite(quantity) &&
                quantity > 0
            ) {
                totalElement.textContent =
                    "₹" + (price * quantity).toFixed(2);
            } else {
                totalElement.textContent = "₹0.00";
            }
        }

        quantityInput.addEventListener("input", updateOrderTotal);
        updateOrderTotal();
    }


    // 6. Crop search input: clear button support
    const clearSearchButton = document.getElementById("clear-search");
    const searchInput = document.getElementById("crop-search");

    if (clearSearchButton && searchInput) {
        clearSearchButton.addEventListener("click", function () {
            searchInput.value = "";
            searchInput.focus();
        });
    }


    // 7. Update character count for textareas
    const countedTextareas = document.querySelectorAll(
        "textarea[data-max-length]"
    );

    countedTextareas.forEach(function (textarea) {
        const maxLength = parseInt(
            textarea.dataset.maxLength,
            10
        );

        const counter = document.getElementById(
            textarea.dataset.counter
        );

        if (!counter || !Number.isFinite(maxLength)) {
            return;
        }

        function updateCharacterCount() {
            counter.textContent =
                textarea.value.length + " / " + maxLength;

            if (textarea.value.length > maxLength) {
                counter.classList.add("text-danger");
            } else {
                counter.classList.remove("text-danger");
            }
        }

        textarea.addEventListener("input", updateCharacterCount);
        updateCharacterCount();
    });


    // 8. Prevent accidental double submission
    const submitForms = document.querySelectorAll(
        "form[data-prevent-double-submit]"
    );

    submitForms.forEach(function (form) {
        form.addEventListener("submit", function () {
            if (!form.checkValidity()) {
                return;
            }

            const submitButton = form.querySelector(
                'button[type="submit"], input[type="submit"]'
            );

            if (submitButton) {
                submitButton.disabled = true;

                if (submitButton.tagName === "BUTTON") {
                    submitButton.dataset.originalText =
                        submitButton.textContent;

                    submitButton.textContent = "Please wait...";
                }
            }
        });
    });


    // 9. KisanSetu Helpdesk Chatbot Controller
    const chatToggle = document.getElementById("kisansetu-chat-toggle");
    const chatBox = document.getElementById("kisansetu-chat-box");
    const chatClose = document.getElementById("kisansetu-chat-close");
    const chatForm = document.getElementById("kisansetu-chat-form");
    const chatInput = document.getElementById("kisansetu-chat-input");
    const chatMessages = document.getElementById("kisansetu-chat-messages");

    if (chatToggle && chatBox) {
        chatToggle.addEventListener("click", function () {
            const isHidden = chatBox.classList.contains("d-none");
            if (isHidden) {
                chatBox.classList.remove("d-none");
                chatInput.focus();
                chatMessages.scrollTop = chatMessages.scrollHeight;
            } else {
                chatBox.classList.add("d-none");
            }
        });

        if (chatClose) {
            chatClose.addEventListener("click", function () {
                chatBox.classList.add("d-none");
            });
        }

        function scrollToBottom() {
            setTimeout(function () {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 60);
        }

        function appendUserMessage(text) {
            const msgDiv = document.createElement("div");
            msgDiv.className = "chat-message user mb-3";
            msgDiv.innerHTML = `
                <div class="message-bubble">
                    ${escapeHtml(text)}
                </div>
            `;
            chatMessages.appendChild(msgDiv);
            scrollToBottom();
        }

        function appendBotMessage(htmlContent, suggestions) {
            const msgDiv = document.createElement("div");
            msgDiv.className = "chat-message bot mb-3";
            msgDiv.innerHTML = `
                <div class="d-flex gap-2">
                    <div class="rounded-circle bg-success text-white d-flex align-items-center justify-content-center flex-shrink-0" style="width: 32px; height: 32px; font-size: 15px;">🌾</div>
                    <div class="message-bubble">
                        ${htmlContent}
                    </div>
                </div>
            `;
            chatMessages.appendChild(msgDiv);

            if (suggestions && suggestions.length > 0) {
                const suggDiv = document.createElement("div");
                suggDiv.className = "d-flex flex-wrap gap-1 mb-2 ps-4";
                suggestions.forEach(function (s) {
                    const btn = document.createElement("button");
                    btn.type = "button";
                    btn.className = "suggestion-btn";
                    btn.textContent = s;
                    btn.dataset.query = s;
                    btn.addEventListener("click", function () {
                        sendMessage(s);
                    });
                    suggDiv.appendChild(btn);
                });
                chatMessages.appendChild(suggDiv);
            }

            scrollToBottom();
        }

        function showTypingIndicator() {
            const typingDiv = document.createElement("div");
            typingDiv.id = "chat-typing-loader";
            typingDiv.className = "chat-message bot mb-3";
            typingDiv.innerHTML = `
                <div class="d-flex gap-2 align-items-center">
                    <div class="rounded-circle bg-success text-white d-flex align-items-center justify-content-center flex-shrink-0" style="width: 32px; height: 32px; font-size: 15px;">🌾</div>
                    <div class="chat-typing-bubble">
                        <span class="chat-typing-dot"></span>
                        <span class="chat-typing-dot"></span>
                        <span class="chat-typing-dot"></span>
                    </div>
                </div>
            `;
            chatMessages.appendChild(typingDiv);
            scrollToBottom();
            return typingDiv;
        }

        function removeTypingIndicator() {
            const loader = document.getElementById("chat-typing-loader");
            if (loader) {
                loader.remove();
            }
        }

        function escapeHtml(text) {
            const div = document.createElement("div");
            div.textContent = text;
            return div.innerHTML;
        }

        async function sendMessage(text) {
            const cleanText = text.trim();
            if (!cleanText) return;

            appendUserMessage(cleanText);
            chatInput.value = "";
            showTypingIndicator();

            try {
                const response = await fetch("/api/chatbot", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ message: cleanText }),
                });

                removeTypingIndicator();

                if (!response.ok) {
                    throw new Error("Network response was not ok");
                }

                const data = await response.json();
                appendBotMessage(data.response, data.suggestions);
            } catch (err) {
                removeTypingIndicator();
                appendBotMessage(
                    "माफ़ कीजिए, कनेक्शन में समस्या आ रही है। कृपया थोड़ी देर बाद पुनः प्रयास करें या हमारे <a href='/help-requests' class='text-success fw-bold'>Help Desk</a> पर संपर्क करें।",
                    ["🏛️ सरकारी योजनाएं", "🌾 फसल कैसे बेचें?", "💬 सहायता केंद्र"]
                );
            }
        }

        document.querySelectorAll(".suggestion-btn").forEach(function (btn) {
            btn.addEventListener("click", function () {
                const query = btn.dataset.query || btn.textContent.trim();
                sendMessage(query);
            });
        });

        chatForm.addEventListener("submit", function (e) {
            e.preventDefault();
            sendMessage(chatInput.value);
        });
    }

});