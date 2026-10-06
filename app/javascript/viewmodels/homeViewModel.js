import { renderHomeView } from "../views/homeView.js";


export function createHomeViewModel() {

    async function mount() {

        const appcontent = document.getElementById("app");

        appcontent.innerHTML = renderHomeView();
    }


    return {
        mount
    };
}