document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const queryInput = document.getElementById("query-input");
    const sendBtn = document.getElementById("send-btn");
    const messagesContainer = document.getElementById("messages-container");
    const clearChatBtn = document.getElementById("clear-chat-btn");
    const quickButtons = document.querySelectorAll(".quick-btn");

    // Modal elements
    const snippetModal = document.getElementById("snippet-modal");
    const closeModalBtn = document.getElementById("close-modal-btn");
    const modalDocId = document.getElementById("modal-doc-id");
    const modalTitle = document.getElementById("modal-title");
    const modalSection = document.getElementById("modal-section");
    const modalSnippet = document.getElementById("modal-snippet");

    // Sidebar status
    const vectorStatusEl = document.getElementById("vector-status");
    const modelNameEl = document.getElementById("model-name");

    // Fetch initial health info
    fetch("/health")
        .then(res => res.json())
        .then(data => {
            if (data.status === "healthy") {
                vectorStatusEl.textContent = `ChromaDB (${data.indexed_chunks} chunks)`;
                if (data.chat_model) {
                    const shortModel = data.chat_model.split("/").pop().replace(":free", "");
                    modelNameEl.textContent = shortModel;
                }
            }
        })
        .catch(err => {
            console.warn("Health check call failed:", err);
        });

    // Auto-expand textarea
    queryInput.addEventListener("input", function() {
        this.style.height = "auto";
        this.style.height = (this.scrollHeight) + "px";
    });

    queryInput.addEventListener("keydown", function(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event("submit"));
        }
    });

    // Quick questions
    quickButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const query = btn.getAttribute("data-query");
            queryInput.value = query;
            queryInput.style.height = "auto";
            chatForm.dispatchEvent(new Event("submit"));
        });
    });

    // Clear chat
    clearChatBtn.addEventListener("click", () => {
        messagesContainer.innerHTML = `
            <div class="message-bubble bot-message intro-bubble">
                <div class="avatar">✦</div>
                <div class="message-content">
                    <p><strong>Chat cleared.</strong> How can I help you with our company policies?</p>
                </div>
            </div>
        `;
    });

    // Submit handler
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const question = queryInput.value.trim();
        if (!question) return;

        // Append user message
        appendUserMessage(question);
        queryInput.value = "";
        queryInput.style.height = "auto";
        sendBtn.disabled = true;

        // Append typing indicator
        const typingBubble = appendTypingIndicator();
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: question })
            });

            const data = await response.json();
            typingBubble.remove();

            if (response.ok && data.status === "success") {
                appendBotMessage(data.answer, data.citations, data.latency_ms, data.model);
            } else {
                appendErrorMessage(data.error || "An error occurred while communicating with the assistant.");
            }
        } catch (err) {
            typingBubble.remove();
            appendErrorMessage("Network error: Unable to reach the policy assistant server.");
            console.error(err);
        } finally {
            sendBtn.disabled = false;
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    });

    function appendUserMessage(text) {
        const bubble = document.createElement("div");
        bubble.className = "message-bubble user-message";
        bubble.innerHTML = `
            <div class="avatar">U</div>
            <div class="message-content">
                <p>${escapeHtml(text)}</p>
            </div>
        `;
        messagesContainer.appendChild(bubble);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function appendTypingIndicator() {
        const bubble = document.createElement("div");
        bubble.className = "message-bubble bot-message";
        bubble.innerHTML = `
            <div class="avatar">✦</div>
            <div class="message-content">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        messagesContainer.appendChild(bubble);
        return bubble;
    }

    function appendBotMessage(answer, citations, latencyMs, model) {
        const bubble = document.createElement("div");
        bubble.className = "message-bubble bot-message";

        // Format bold text and citations
        let formattedAnswer = escapeHtml(answer)
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\n\n/g, "</p><p>")
            .replace(/\n/g, "<br>");

        let citationsHtml = "";
        if (citations && citations.length > 0) {
            citationsHtml = `
                <div class="citations-box">
                    <div class="citations-label">Verified Source Excerpts:</div>
                    <div class="citations-list">
                        ${citations.map((c, idx) => `
                            <button class="citation-chip" data-idx="${idx}">
                                <span>📄</span> ${escapeHtml(c.doc_id)}: ${escapeHtml(c.section)}
                            </button>
                        `).join("")}
                    </div>
                </div>
            `;
        }

        const shortModel = model ? model.split("/").pop().replace(":free", "") : "Cloud LLM";

        bubble.innerHTML = `
            <div class="avatar">✦</div>
            <div class="message-content">
                <p>${formattedAnswer}</p>
                ${citationsHtml}
                <div class="message-meta">
                    <span>⚡ ${latencyMs}ms</span>
                    <span>•</span>
                    <span>Model: ${escapeHtml(shortModel)}</span>
                </div>
            </div>
        `;

        messagesContainer.appendChild(bubble);

        // Attach click handlers to citation chips
        if (citations && citations.length > 0) {
            const chips = bubble.querySelectorAll(".citation-chip");
            chips.forEach((chip, i) => {
                chip.addEventListener("click", () => {
                    openSnippetModal(citations[i]);
                });
            });
        }

        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function appendErrorMessage(errorMsg) {
        const bubble = document.createElement("div");
        bubble.className = "message-bubble bot-message";
        bubble.innerHTML = `
            <div class="avatar" style="background: #ef4444;">!</div>
            <div class="message-content" style="border-color: #ef4444; background: rgba(239, 68, 68, 0.1);">
                <p><strong>System Notice:</strong> ${escapeHtml(errorMsg)}</p>
            </div>
        `;
        messagesContainer.appendChild(bubble);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Modal controls
    function openSnippetModal(citation) {
        modalDocId.textContent = citation.doc_id;
        modalTitle.textContent = citation.title;
        modalSection.textContent = citation.section;
        modalSnippet.textContent = citation.snippet;
        snippetModal.classList.remove("hidden");
    }

    function closeModal() {
        snippetModal.classList.add("hidden");
    }

    closeModalBtn.addEventListener("click", closeModal);
    snippetModal.addEventListener("click", (e) => {
        if (e.target === snippetModal) {
            closeModal();
        }
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && !snippetModal.classList.contains("hidden")) {
            closeModal();
        }
    });

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }
});
