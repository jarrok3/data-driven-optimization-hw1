import { router } from "./router.js";
// Event listeners are native html/js functions.  

document.addEventListener("DOMContentLoaded", () => {
    router();
});


document.addEventListener("click", (event) => {

    const link = event.target.closest("[data-link]");

    if (!link) {
        return;
    }

    event.preventDefault();

    const url = link.getAttribute("href");

    history.pushState({}, "", url);

    router();
});


window.addEventListener("popstate", () => {
    router();
});