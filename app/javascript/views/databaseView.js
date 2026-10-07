export function renderDatabaseView(state) {
    const rows = state.records
        .map(record => `
            <tr>
                <td>${record.id}</td>
                <td>${record.title_tag}</td>
                <td>${record.venue_tag}</td>
                <td>${record.play_day}</td>
                <td>${record.curtain_time}</td>
                <td>${record.account_tag}</td>
                <td>${record.passes_bought}</td>
            </tr>
        `)
        .join("");

    return `
        <section>

            <h1>Database Browser</h1>

            ${
                state.error
                    ? `<p>${state.error}</p>`
                    : ""
            }

            <p>
                Historical cinema data - dummy data created for the purpose of the PoC.
            </p>

            <div id="database-content">
                <table>

                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>TITLE</th>
                            <th>CINEMA_TAG</th>
                            <th>PLAY_DAY</th>
                            <th>CURTAIN_TIME</th>
                            <th>ACCOUNT_TAG</th>
                            <th>PASSES_BOUGHT</th>
                        </tr>
                    </thead>

                    <tbody>
                        ${rows}
                    </tbody>

                </table>

                ${
                    state.loading
                        ? "<p>Loading...</p>"
                        : "<p>No data loaded yet.</p>"
                }

            </div>

        </section>
    `;
}