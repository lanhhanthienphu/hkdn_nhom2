// Dong menu sau khi chon mot muc tren dien thoai.
document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("sidebar");
    if (!sidebar || !window.bootstrap) return;

    sidebar.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", (event) => {
            if (!window.matchMedia("(max-width: 991.98px)").matches) return;

            const menu = window.bootstrap.Offcanvas.getInstance(sidebar);
            if (!menu || !sidebar.classList.contains("show")) return;

            const destination = new URL(link.href);
            const target = destination.pathname === window.location.pathname
                ? document.getElementById(destination.hash.slice(1))
                : null;

            if (target) {
                event.preventDefault();
                sidebar.addEventListener("hidden.bs.offcanvas", () => {
                    window.history.pushState(null, "", destination.href);
                    target.setAttribute("tabindex", "-1");
                    target.focus({ preventScroll: true });
                    target.scrollIntoView();
                }, { once: true });
            }
            menu.hide();
        });
    });
});
