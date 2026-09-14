let adminMessages = [];
let selectedMessage = null;

async function loadMessages(showToastMessage = false) {
    try {
        const data = await api("/admin/messages");

        if (!data || !data.success) {
            throw new Error(data?.message || "Unable to load messages");
        }

        adminMessages = Array.isArray(data.messages) ? data.messages : [];

        updateMessageBadge();
        renderMessages();

        if (showToastMessage && typeof showToast === "function") {
            showToast("Customer messages refreshed");
        }
    } catch (error) {
        console.error("Messages error:", error);

        const box = document.getElementById("messagesList");

        if (box) {
            box.innerHTML =
                '<div class="empty">Unable to load customer messages.</div>';
        }
    }
}

function updateMessageBadge() {
    const badge = document.getElementById("messageBadge");

    if (!badge) return;

    const count = adminMessages.length;

    if (count > 0) {
        badge.textContent = count > 99 ? "99+" : count;
        badge.classList.remove("hidden");
    } else {
        badge.classList.add("hidden");
    }
}

function renderMessages() {
    const box = document.getElementById("messagesList");

    if (!box) return;

    if (!adminMessages.length) {
        box.innerHTML =
            '<div class="empty">No customer messages found.</div>';
        return;
    }

    box.innerHTML = adminMessages.map(function(message) {
        const name = escapeHtml(message.name || "Customer");
        const email = escapeHtml(message.email || "");
        const text = escapeHtml(message.message || "");
        const id = Number(message.id);

        let dateText = "";

        if (message.created_at) {
            const d = new Date(message.created_at);

            if (!isNaN(d.getTime())) {
                dateText = d.toLocaleString();
            } else {
                dateText = escapeHtml(message.created_at);
            }
        }

        const initial = escapeHtml(
            (message.name || "C").charAt(0).toUpperCase()
        );

        return `
            <div class="message-card">
                <div class="message-top">
                    <div class="message-customer">
                        <div class="message-avatar">${initial}</div>

                        <div>
                            <div class="message-name">${name}</div>
                            <div class="message-email">${email}</div>
                        </div>
                    </div>

                    <div class="message-date">${dateText}</div>
                </div>

                <div class="message-body">${text}</div>

                <div class="message-actions">
                    <button
                        class="reply-btn"
                        onclick="openReplyModal(${id})">
                        ↩ Reply
                    </button>
                </div>
            </div>
        `;
    }).join("");
}

function openReplyModal(id) {
    selectedMessage = adminMessages.find(function(message) {
        return Number(message.id) === Number(id);
    });

    if (!selectedMessage) {
        showToast("Message not found");
        return;
    }

    document.getElementById("replyCustomer").textContent =
        (selectedMessage.name || "Customer") +
        " • " +
        (selectedMessage.email || "");

    document.getElementById("replyOriginal").textContent =
        selectedMessage.message || "";

    document.getElementById("replyText").value = "";

    document.getElementById("replyModal").classList.remove("hidden");

    setTimeout(function() {
        document.getElementById("replyText").focus();
    }, 100);
}

function closeReplyModal() {
    const modal = document.getElementById("replyModal");

    if (modal) {
        modal.classList.add("hidden");
    }

    selectedMessage = null;
}

async function sendAdminReply() {
    if (!selectedMessage) return;

    const input = document.getElementById("replyText");
    const reply = input.value.trim();

    if (!reply) {
        showToast("Please type a reply");
        input.focus();
        return;
    }

    try {
        const data = await api(
            "/admin/messages/" + Number(selectedMessage.id) + "/reply",
            {
                method: "POST",
                body: JSON.stringify({
                    reply: reply
                })
            }
        );

        if (!data || !data.success) {
            throw new Error(data?.message || "Reply failed");
        }

        closeReplyModal();
        showToast("Reply sent to customer");

    } catch (error) {
        console.error("Reply error:", error);
        showToast(
            "Reply failed: " + (error.message || "Unknown error")
        );
    }
}

document.addEventListener("DOMContentLoaded", function() {
    setTimeout(function() {
        loadMessages(false);
    }, 500);

    setInterval(function() {
        loadMessages(false);
    }, 30000);

    document.addEventListener("click", function(event) {
        const modal = document.getElementById("replyModal");

        if (modal && event.target === modal) {
            closeReplyModal();
        }
    });
});
