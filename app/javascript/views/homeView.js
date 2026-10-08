function renderScheduleTable(schedule) {

    if (!schedule || schedule.length === 0) {
        return `
            <p>
                Schedule is empty.
            </p>
        `;
    }

    const rows = schedule
        .map(screening => `
            <tr>

                <td>
                    ${screening.day}
                </td>

                <td>
                    ${screening.start_time}
                </td>

                <td>
                    ${screening.room}
                </td>

                <td>
                    ${screening.title}
                </td>

                <td>
                    ${screening.required_blocks}
                </td>

                <td>
                    ${screening.occupied_slots.join(", ")}
                </td>

            </tr>
        `)
        .join("");

    return `
        <table class="schedule-table">

            <thead>
                <tr>
                    <th>Day</th>
                    <th>Start time</th>
                    <th>Room</th>
                    <th>Movie</th>
                    <th>Required blocks</th>
                    <th>Occupied slots</th>
                </tr>
            </thead>

            <tbody>
                ${rows}
            </tbody>

        </table>
    `;
}

function renderScheduleResult(
    result,
    title
) {

    if (!result) {
        return "";
    }

    return `
        <section class="schedule-result">

            <h2>
                ${title}
            </h2>

            <p>
                Status:
                <strong>
                    ${result.status}
                </strong>
            </p>

            ${
                result.objective_value !== undefined
                    ? `
                        <p>
                            Expected total attendance:
                            <strong>
                                ${Math.round(
                                    result.objective_value
                                )}
                            </strong>
                        </p>
                    `
                    : ""
            }

            ${renderScheduleTable(
                result.schedule
            )}

        </section>
    `;
}

export function renderHomeView(state) {

    const repertoireRows = state.repertoire
        .map((movie, index) => `
            <tr>
                <td>
                    <input
                        type="text"
                        value="${movie.title}"
                        data-field="title"
                        data-index="${index}"
                        placeholder="Movie title"
                    >
                </td>

                <td>
                    <select
                        data-field="required_blocks"
                        data-index="${index}"
                    >
                        <option
                            value="1"
                            ${movie.required_blocks === 1 ? "selected" : ""}
                        >
                            1
                        </option>

                        <option
                            value="2"
                            ${movie.required_blocks === 2 ? "selected" : ""}
                        >
                            2
                        </option>
                    </select>
                </td>

                <td>
                    <button
                        type="button"
                        data-action="remove-movie"
                        data-index="${index}"
                        class="danger-button"
                    >
                        Remove
                    </button>
                </td>
            </tr>
        `)
        .join("");


    const dayInputs = Object.entries(state.advanced.dayWeights)
        .map(([day, value]) => `
            <div class="advanced-option-row">
                <label>${day}</label>

                <input
                    type="number"
                    step="0.05"
                    min="0"
                    value="${value}"
                    data-advanced-type="day"
                    data-key="${day}"
                >
            </div>
        `)
        .join("");


    const timeInputs = Object.entries(state.advanced.timeWeights)
        .map(([time, value]) => `
            <div class="advanced-option-row">
                <label>${time}</label>

                <input
                    type="number"
                    step="0.05"
                    min="0"
                    value="${value}"
                    data-advanced-type="time"
                    data-key="${time}"
                >
            </div>
        `)
        .join("");


    return `
        <section class="home-panel">

            <h1>Movie Programming - Assignment 1 demo</h1>

            <p>
                Single cinema schedule optimization demo.
            </p>


            <!-- REPERTOIRE -->

            <section class="panel-section">

                <h2>Repertoire</h2>
                Please use this section to input your own movie repertoire for the upcoming week.

                <table class="repertoire-table">

                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Required blocks</th>
                            <th></th>
                        </tr>
                    </thead>

                    <tbody>
                        ${repertoireRows}
                    </tbody>

                </table>

                <div class="repertoire-actions">
                    <button
                        type="button"
                        data-action="use-model-repertoire"
                        class="preset-button"
                    >
                        Use model repertoire
                    </button>

                    <button
                        type="button"
                        data-action="reset-defaults"
                        class="reset-button"
                    >
                        Reset to defaults
                    </button>

                    <button
                        type="button"
                        data-action="add-movie"
                        class="secondary-button"
                    >
                        + Add movie
                    </button>

                </div>

            </section>


            <!-- ROOMS -->

            <section class="panel-section">

                <h2>Room amount</h2>

                <div class="room-counter">

                    <button
                        type="button"
                        data-action="decrease-rooms"
                    >
                        −
                    </button>

                    <span class="room-count">
                        ${state.roomAmount}
                    </span>

                    <button
                        type="button"
                        data-action="increase-rooms"
                    >
                        +
                    </button>

                </div>

                <small>
                    Allowed range: 1–8 rooms
                </small>

            </section>
    
                </br>

            <!-- ADVANCED OPTIONS -->

            <section class="panel-section">

                <button
                    type="button"
                    data-action="toggle-advanced"
                    class="advanced-toggle"
                >
                    ${state.advanced.visible
                        ? "Hide advanced options"
                        : "Advanced options"}
                </button>


                ${
                    state.advanced.visible
                        ? `
                            <div class="advanced-options">

                                <div class="advanced-column">

                                    <h3>Day weights</h3>

                                    ${dayInputs}

                                </div>


                                <div class="advanced-column">

                                    <h3>Time-slot weights</h3>

                                    ${timeInputs}

                                </div>

                            </div>
                        `
                        : ""
                }

            </section>

                </br>
            <!-- GENERATE -->

            <section class="generate-section">
                <button
                    type="button"
                    data-action="generate-baseline"
                    class="secondary-button"
                    ${state.baselineLoading ? "disabled" : ""}
                >
                    ${
                        state.baselineLoading
                            ? "GENERATING BASELINE..."
                            : "GENERATE BASELINE"
                    }
                </button>

                <button
                    type="button"
                    data-action="generate-optimized"
                    class="preset-button"
                    ${state.optimizedLoading ? "disabled" : ""}
                >
                    ${
                        state.optimizedLoading
                            ? "OPTIMIZING..."
                            : "GENERATE OPTIMIZED"
                    }
                </button>
            </section>

            ${state.error
                ? `
                    <div class="error-message">
                        ${state.error}
                    </div>
                `
                : ""
            }

            ${renderScheduleResult(
                state.baselineResult,
                "Baseline schedule"
            )}

            ${renderScheduleResult(
                state.optimizedResult,
                "CP-SAT optimized schedule"
            )}

        </section>
    `;
}