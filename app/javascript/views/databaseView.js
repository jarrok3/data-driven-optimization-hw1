export function renderDatabaseView(state) {
    const rows = state.records
        .map(record => `
            <tr>
                <td>${record.id}</td>
                <td>${record.title}</td>
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
                            <th>col1</th>
                            <th>col2</th>
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