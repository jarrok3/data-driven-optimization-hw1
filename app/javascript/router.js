import { createHomeViewModel } from "./viewmodels/homeViewModel.js";
import { createDatabaseViewModel } from "./viewmodels/databaseViewModel.js";


export async function router() {

    const path = window.location.pathname;

    if (path === "/") {
        const viewModel = createHomeViewModel();
        await viewModel.mount();
        return;
    }

    if (path === "/database") {
        const viewModel = createDatabaseViewModel();
        await viewModel.mount();
        return;
    }

    document.getElementById("app").innerHTML = `
        <h1>404</h1>
        <p>Page not found.</p>
    `;
}