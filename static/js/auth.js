document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-password-toggle]").forEach((button) => {
        const input = document.getElementById(button.dataset.passwordToggle);
        if (!input) return;
        const label = button.getAttribute("aria-label").replace(/^Hiện /, "");
        button.hidden = false;
        button.addEventListener("click", () => {
            const reveal = input.type === "password";
            input.type = reveal ? "text" : "password";
            button.textContent = reveal ? "Ẩn" : "Hiện";
            button.setAttribute("aria-pressed", String(reveal));
            button.setAttribute("aria-label", `${reveal ? "Ẩn" : "Hiện"} ${label}`);
        });
    });
    const errors = document.querySelector("[data-error-summary]");
    if (errors) errors.focus();
});
