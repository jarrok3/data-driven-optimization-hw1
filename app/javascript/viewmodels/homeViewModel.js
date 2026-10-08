import { renderHomeView } from "../views/homeView.js";
import {
    generateSchedule,
    generateBaselineSchedule
} from "../services/apiService.js";

const DEFAULT_REPERTOIRE = [
    {
        title: "",
        required_blocks: 1
    }
];


const MODEL_REPERTOIRE = [
    {
        title: "TITLE_A",
        required_blocks: 1
    },
    {
        title: "TITLE_B",
        required_blocks: 2
    },
    {
        title: "TITLE_C",
        required_blocks: 1
    },
    {
        title: "TITLE_D",
        required_blocks: 1
    },
    {
        title: "NEW_TITLE_A",
        required_blocks: 1
    },
    {
        title: "NEW_TITLE_B",
        required_blocks: 2
    }
];

export function createHomeViewModel() {

    const state = {

        repertoire: [
            {
                title: "",
                required_blocks: 1
            }
        ],

        optimizedResult: null,
        baselineResult: null,

        optimizedLoading: false,
        baselineLoading: false,

        error: null,

        roomAmount: 1,

        advanced: {

            visible: false,

            dayWeights: {
                Monday: 1.00,
                Tuesday: 1.00,
                Wednesday: 1.00,
                Thursday: 1.00,
                Friday: 1.30,
                Saturday: 1.50,
                Sunday: 1.35
            },

            timeWeights: {
                "10:00": 0.30,
                "12:00": 0.40,
                "14:00": 0.60,
                "16:00": 1.00,
                "18:00": 1.50,
                "20:00": 1.80,
                "22:00": 1.10
            }
        }
    };

    async function generateOptimized() {

    state.optimizedLoading = true;
    state.error = null;
    state.optimizedResult = null;

    render();

    try {

        const requestData =
            buildRequestData();

        state.optimizedResult =
            await generateSchedule(
                requestData
            );

        console.log(
            "Optimized result:",
            state.optimizedResult
        );

    } catch (error) {

        console.error(error);

        state.error =
            error.message;

    } finally {

        state.optimizedLoading = false;

        render();
    }
    }

    async function generateBaseline() {

    state.baselineLoading = true;
    state.error = null;
    state.baselineResult = null;

    render();

    try {

        const requestData =
            buildRequestData();

        state.baselineResult =
            await generateBaselineSchedule(
                requestData
            );

        console.log(
            "Baseline result:",
            state.baselineResult
        );

    } catch (error) {

        console.error(error);

        state.error =
            error.message;

    } finally {

        state.baselineLoading = false;

        render();
    }
    }

    function buildRequestData() {
        return {

            repertoire: state.repertoire.map(
                movie => ({
                    title: movie.title.trim(),
                    required_blocks:
                        Number(movie.required_blocks)
                })
            ),

            room_amount:
                state.roomAmount,

            day_weights:
                state.advanced.dayWeights,

            time_weights:
                state.advanced.timeWeights
        };
    }

    function render() {

        const app = document.getElementById("app");

        app.innerHTML = renderHomeView(state);
    }

    function useModelRepertoire() {

        state.repertoire = MODEL_REPERTOIRE.map(movie => ({
            ...movie
        }));

        render();
    }


    function resetToDefaults() {

        state.repertoire = DEFAULT_REPERTOIRE.map(movie => ({
            ...movie
        }));

        state.roomAmount = 1;

        state.advanced.visible = false;

        state.advanced.dayWeights = {
            Monday: 1.00,
            Tuesday: 1.00,
            Wednesday: 1.00,
            Thursday: 1.00,
            Friday: 1.30,
            Saturday: 1.50,
            Sunday: 1.35
        };

        state.advanced.timeWeights = {
            "10:00": 0.30,
            "12:00": 0.40,
            "14:00": 0.60,
            "16:00": 1.00,
            "18:00": 1.50,
            "20:00": 1.80,
            "22:00": 1.10
        };

        state.baselineResult = null;
        state.optimizedResult = null;

        state.baselineLoading = false;
        state.optimizedLoading = false;

        state.error = null;

        render();
    }

    function addMovie() {

        state.repertoire.push({
            title: "",
            required_blocks: 1
        });

        render();
    }


    function removeMovie(index) {

        if (state.repertoire.length <= 1) {
            return;
        }

        state.repertoire.splice(index, 1);

        render();
    }


    function increaseRooms() {

        if (state.roomAmount < 8) {
            state.roomAmount += 1;
            render();
        }
    }


    function decreaseRooms() {

        if (state.roomAmount > 1) {
            state.roomAmount -= 1;
            render();
        }
    }


    function toggleAdvanced() {

        state.advanced.visible =
            !state.advanced.visible;

        render();
    }

    function handleClick(event) {

        const target =
            event.target.closest("[data-action]");

        if (!target) {
            return;
        }

        const action =
            target.dataset.action;

        const index =
            Number(target.dataset.index);


        switch (action) {

            case "add-movie":
                addMovie();
                break;

            case "remove-movie":
                removeMovie(index);
                break;

            case "increase-rooms":
                increaseRooms();
                break;

            case "decrease-rooms":
                decreaseRooms();
                break;

            case "toggle-advanced":
                toggleAdvanced();
                break;

            case "use-model-repertoire":
                useModelRepertoire();
                break;

            case "reset-defaults":
                resetToDefaults();
                break;

            case "generate-optimized":
                generateOptimized();
                break;

            case "generate-baseline":
                generateBaseline();
                break;
        }
    }


    function handleInput(event) {

        const target = event.target;


        /*
            REPERTOIRE
        */

        if (target.dataset.field) {

            const index =
                Number(target.dataset.index);

            const field =
                target.dataset.field;


            if (field === "title") {

                state.repertoire[index].title =
                    target.value;
            }


            if (field === "required_blocks") {

                state.repertoire[index].required_blocks =
                    Number(target.value);
            }

            return;
        }


        /*
            ADVANCED OPTIONS
        */

        if (target.dataset.advancedType) {

            const type =
                target.dataset.advancedType;

            const key =
                target.dataset.key;

            const value =
                Number(target.value);


            if (type === "day") {

                state.advanced.dayWeights[key] =
                    value;
            }


            if (type === "time") {

                state.advanced.timeWeights[key] =
                    value;
            }
        }
    }


    async function mount() {
        window.onscroll = null;
        render();

        const app =
            document.getElementById("app");

        /*
            Using onclick/oninput rather than addEventListener
            prevents duplicated listeners when this view
            is mounted again.
        */

        app.onclick = handleClick;

        app.oninput = handleInput;
    }


    return {
        mount
    };
}