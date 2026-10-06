import { renderDatabaseView } from "../views/databaseView.js";
import { getRecords } from "../services/apiService.js";

export function createDatabaseViewModel() {
    const state = {
        records: [],
        loading: false,
        error: null,
        offset: 0,
        limit: 50,
        hasMore: true
    };

    function render(){
        const appcontent = document.getElementById("app");
        appcontent.innerHTML = renderDatabaseView(state);
    }

    async function loadDatabaseContent(){
        state.loading = true;
        render();

        // LAZY LOAD implementation. getRecords() stems from the service layer.
        try {
            const records = await getRecords(
                state.offset,
                state.limit
            );

            state.records.push(...records);
            state.offset += state.limit;
        }
        catch (error) {
            state.error = error.message;
        }
        finally {
            state.loading = false;
            render();
        }
    }

    async function mount()
    {
        render();
        await loadDatabaseContent();
    }

    return{
        mount,
        loadDatabaseContent
    };
}