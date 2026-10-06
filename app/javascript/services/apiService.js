export async function getRecords(
    offset = 0,
    limit = 50
) {

    const response = await fetch(
        `/api/records?offset=${offset}&limit=${limit}`
    );


    if (!response.ok) {

        throw new Error(
            "Could not load movies."
        );

    }

    const data = await response.json();

    return data.map(record =>
        new Record(
            record.id,
            movie.title
        )
    );
}