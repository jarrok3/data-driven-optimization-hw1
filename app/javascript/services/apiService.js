import { Record } from "../models/dbrecord.js";

export async function getRecords(
    offset = 0,
    limit = 50
) {

    const response = await fetch(
        `/api/records?offset=${offset}&limit=${limit}`
    );


    if (!response.ok) {

        const errorText = await response.text();

        console.error(
            "API error:",
            response.status,
            response.statusText,
            errorText
        );

        throw new Error(
            `Could not load records. HTTP ${response.status}`
        );

    }

    const data = await response.json();

    return data.map(record =>
        new Record(
            record.id,
            record.title_tag,
            record.venue_tag,
            record.play_day,
            record.curtain_time,
            record.account_tag,
            record.passes_bought
        )
    );
}