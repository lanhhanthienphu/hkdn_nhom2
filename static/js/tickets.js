// Progressive enhancement: forms, filters, and pagination also work without JS.
document.addEventListener("DOMContentLoaded", () => {
    const summary = document.querySelector("[data-error-summary]");
    if (summary) summary.focus();

    const description = document.querySelector("[data-character-count]");
    const counter = document.querySelector("[data-count-output]");
    if (description && counter) {
        counter.hidden = false;
        const updateCount = () => {
            counter.textContent = `${Array.from(description.value).length.toLocaleString("vi-VN")} / 5.000 ký tự`;
        };
        description.addEventListener("input", updateCount);
        updateCount();
    }

    const input = document.querySelector("input[type=file][data-max-bytes]");
    const feedback = document.querySelector("[data-file-feedback]");
    if (input && feedback) {
        const remove = document.querySelector("[data-remove-file]");
        const preview = document.querySelector("[data-file-preview]");
        const previewImage = document.querySelector("[data-preview-image]");
        let previewUrl = null;
        const clearPreview = () => {
            if (previewUrl) URL.revokeObjectURL(previewUrl);
            previewUrl = null;
            if (preview) preview.hidden = true;
            if (previewImage) previewImage.removeAttribute("src");
        };
        const updateFile = () => {
            const file = input.files[0];
            clearPreview();
            input.setCustomValidity("");
            feedback.classList.remove("is-error");
            feedback.textContent = "";
            if (remove) remove.hidden = !file;
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
                if (preview && previewImage && /^(image\/png|image\/jpeg)$/i.test(file.type)) {
                    previewUrl = URL.createObjectURL(file);
                    const currentUrl = previewUrl;
                    previewImage.onerror = () => {
                        if (previewUrl === currentUrl) clearPreview();
                    };
                    previewImage.src = previewUrl;
                    preview.hidden = false;
                }
            }
        };
        input.addEventListener("change", updateFile);
        if (remove) remove.addEventListener("click", () => {
            input.value = "";
            updateFile();
            feedback.textContent = "Đã bỏ file đính kèm.";
            input.focus();
        });
        window.addEventListener("pagehide", clearPreview);
        window.addEventListener("pageshow", updateFile);
    }

    const category = document.getElementById("id_category");
    const kbLink = document.querySelector("[data-kb-suggestion]");
    if (category && kbLink) {
        category.addEventListener("change", () => {
            const query = {network: "Wi-Fi", vpn: "VPN", printer: "máy in"}[category.value] || "";
            kbLink.href = kbLink.dataset.kbUrl + (query ? `?q=${encodeURIComponent(query)}` : "");
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
