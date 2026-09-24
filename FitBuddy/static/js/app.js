document.addEventListener("DOMContentLoaded", () => {
    const navToggle = document.querySelector(".nav-toggle");
    const nav = document.querySelector("#site-nav");

    if (navToggle && nav) {
        navToggle.addEventListener("click", () => {
            const open = nav.classList.toggle("is-open");
            navToggle.setAttribute("aria-expanded", String(open));
        });
    }

    document.querySelectorAll(".flash-close").forEach((button) => {
        button.addEventListener("click", () => {
            button.closest(".flash")?.remove();
        });
    });

    document.querySelectorAll("[data-password-toggle]").forEach((button) => {
        button.addEventListener("click", () => {
            const target = document.querySelector(button.dataset.passwordToggle);
            if (!target) return;

            const showing = target.type === "text";
            target.type = showing ? "password" : "text";
            button.textContent = showing ? "Show" : "Hide";
        });
    });

    const generationForm = document.querySelector("[data-generation-form]");
    if (generationForm) {
        generationForm.addEventListener("submit", () => {
            const button = generationForm.querySelector("[data-generation-button]");
            const label = generationForm.querySelector("[data-button-label]");

            if (button) {
                button.classList.add("is-loading");
                button.disabled = true;
            }

            if (label) {
                label.textContent = "Generating your plan…";
            }
        });
    }
});
