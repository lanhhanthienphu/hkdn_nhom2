(() => {
    const root = document.querySelector("[data-chatbot]");
    if (!root) return;

    const bubble = root.querySelector("[data-chatbot-toggle]");
    const panel = root.querySelector("[data-chatbot-panel]");
    const messages = root.querySelector("[data-chatbot-messages]");
    const form = root.querySelector("[data-chatbot-form]");
    const input = root.querySelector("[data-chatbot-input]");
    const status = root.querySelector("[data-chatbot-status]");
    const endpoint = root.dataset.chatUrl;
    const history = [];
    let pending = false;

    const controls = [bubble, ...document.querySelectorAll("[data-chatbot-open]")];
    controls.forEach((button) => {
        button.setAttribute("aria-controls", panel.id);
        button.setAttribute("aria-haspopup", "dialog");
        button.setAttribute("aria-expanded", "false");
    });

    function setOpen(open) {
        panel.hidden = !open;
        controls.forEach((button) => button.setAttribute("aria-expanded", String(open)));
        const label = open ? "Thu gọn khung chat" : "Mở chat với trợ lý Helpdesk";
        bubble.setAttribute("aria-label", label);
        bubble.title = label;
        if (open) {
            const focusTarget = window.matchMedia("(pointer: coarse)").matches ? panel : input;
            focusTarget.focus({ preventScroll: true });
            scrollToLatest();
        } else {
            bubble.focus({ preventScroll: true });
        }
    }

    bubble.addEventListener("click", () => setOpen(panel.hidden));

    function scrollToLatest() {
        messages.scrollTop = messages.scrollHeight;
    }

    function addMessage(text, kind, sourceTitles = []) {
        const message = document.createElement("div");
        message.className = `chatbot-message chatbot-message-${kind}`;
        const content = document.createElement("span");
        content.textContent = text;
        message.append(content);

        if (sourceTitles.length) {
            const source = document.createElement("small");
            source.className = "chatbot-sources";
            source.textContent = `Tham khảo: ${sourceTitles.join(" · ")}`;
            message.append(source);
        }

        messages.append(message);
        scrollToLatest();
        return message;
    }

    function addQuickPrompts() {
        const wrap = document.createElement("div");
        wrap.className = "chatbot-quick-prompts";
        [
            ["Web này dùng để làm gì?", "Web này dùng để làm gì?"],
            ["Mất kết nối Wi-Fi", "Máy tính không kết nối được Wi-Fi"],
            ["Mạng chậm", "Mạng Wi-Fi chậm hoặc chập chờn"],
        ].forEach(([label, prompt]) => {
            const button = document.createElement("button");
            button.type = "button";
            button.dataset.chatbotPrompt = prompt;
            button.textContent = label;
            wrap.append(button);
        });
        messages.append(wrap);
    }

    async function sendMessage(rawText) {
        const text = rawText.trim();
        if (!text || pending) return;

        messages.querySelector(".chatbot-quick-prompts")?.remove();
        addMessage(text, "user");
        input.value = "";
        input.style.height = "auto";
        status.textContent = "Đang soạn câu trả lời…";
        pending = true;
        form.querySelector("button[type='submit']").disabled = true;
        const typing = addMessage("Đang tìm hướng dẫn phù hợp…", "typing");

        try {
            const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;
            const response = await fetch(endpoint, {
                method: "POST",
                credentials: "same-origin",
                headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
                body: JSON.stringify({ message: text, history: history.slice(-6) }),
            });
            const result = await response.json();
            typing.remove();
            if (!response.ok) throw new Error(result.message || "Không gửi được câu hỏi.");

            addMessage(result.answer, "bot", result.sources || []);
            history.push({ role: "user", content: text }, { role: "assistant", content: result.answer });
            status.textContent = "";
        } catch (error) {
            typing.remove();
            addMessage(error.message || "Có lỗi kết nối. Bạn thử gửi lại nhé.", "bot");
            status.textContent = "Chưa gửi được câu hỏi.";
        } finally {
            pending = false;
            form.querySelector("button[type='submit']").disabled = false;
            if (!panel.hidden) {
                if (form.contains(document.activeElement)) input.focus({ preventScroll: true });
                scrollToLatest();
            }
        }
    }

    document.addEventListener("click", (event) => {
        const launcher = event.target.closest("[data-chatbot-open]");
        if (launcher) {
            event.preventDefault();
            if (launcher.dataset.chatbotPrompt && !input.value.trim()) {
                input.value = launcher.dataset.chatbotPrompt;
            }
            const sidebar = launcher.closest("#sidebar.show");
            const menu = sidebar && window.bootstrap?.Offcanvas.getInstance(sidebar);
            if (menu) {
                sidebar.addEventListener("hidden.bs.offcanvas", () => setOpen(true), { once: true });
                menu.hide();
            } else {
                setOpen(true);
            }
            return;
        }

        if (event.target.closest("[data-chatbot-close]")) {
            setOpen(false);
            return;
        }

        const prompt = event.target.closest("[data-chatbot-prompt]");
        if (prompt) sendMessage(prompt.dataset.chatbotPrompt);

        if (event.target.closest("[data-chatbot-clear]")) {
            if (pending) return;
            history.length = 0;
            messages.replaceChildren();
            addMessage("Xin chào! Mình có thể hướng dẫn cách dùng hệ thống và kiểm tra một số lỗi mạng cơ bản. Bạn cần hỗ trợ gì?", "bot");
            addQuickPrompts();
            status.textContent = "Đã bắt đầu cuộc trò chuyện mới.";
            input.focus();
        }
    });

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        sendMessage(input.value);
    });

    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
            event.preventDefault();
            form.requestSubmit();
        }
    });

    input.addEventListener("input", () => {
        input.style.height = "auto";
        input.style.height = `${Math.min(input.scrollHeight, 112)}px`;
    });

    root.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !event.isComposing && !panel.hidden) {
            setOpen(false);
        }
    });
})();
