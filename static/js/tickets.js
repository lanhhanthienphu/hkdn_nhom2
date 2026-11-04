// Progressive enhancement: forms, filters, and pagination also work without JS.
document.addEventListener("DOMContentLoaded", () => {
    const summary = document.querySelector("[data-error-summary]");
    if (summary) summary.focus();

    const description = document.querySelector("[data-character-count]");
    const counter = document.querySelector("[data-count-output]");
    if (description && counter) {
        const updateCount = () => {
            counter.textContent = `${Array.from(description.value).length.toLocaleString("vi-VN")} / 5.000 ký tự`;
        };
        description.addEventListener("input", updateCount);
        updateCount();
    }

    const input = document.querySelector("input[type=file][data-max-bytes]");
    const feedback = document.querySelector("[data-file-feedback]");
    if (input && feedback) {
        input.addEventListener("change", () => {
            const file = input.files[0];
            input.setCustomValidity("");
            feedback.classList.remove("is-error");
            feedback.textContent = "";
            if (!file) return;
            let error = "";
            if (file.size > Number(input.dataset.maxBytes)) error = "File vượt quá 10 MB. Vui lòng chọn file nhỏ hơn.";
            else if (!/\.(jpe?g|png|pdf|txt|log)$/i.test(file.name)) error = "Chỉ chấp nhận file JPG, PNG, PDF, TXT hoặc LOG.";
            if (error) {
                input.setCustomValidity(error);
                feedback.textContent = error;
                feedback.classList.add("is-error");
            } else {
                const size = file.size >= 1024 * 1024
                    ? `${(file.size / (1024 * 1024)).toFixed(1)} MB`
                    : `${Math.max(1, Math.ceil(file.size / 1024))} KB`;
                feedback.textContent = `Đã chọn: ${file.name} (${size}). Nội dung file chưa được lưu trong bản xem thử.`;
            }
        });
    }

    document.querySelectorAll("[data-ticket-form]").forEach((form) => {
        const button = form.querySelector("[data-submit-button]");
        if (!button) return;
        const label = button.innerHTML;
        form.addEventListener("submit", () => {
            if (!form.checkValidity()) return;
            button.disabled = true;
            button.textContent = "Đang xử lý…";
        });
        // Restore the button when returning with the browser's Back button.
        window.addEventListener("pageshow", () => {
            button.disabled = false;
            button.innerHTML = label;
        });
    });
});
