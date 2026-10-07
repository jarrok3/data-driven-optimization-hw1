export class Record {
    constructor(
        id,
        title_tag,
        venue_tag,
        play_day,
        curtain_time,
        account_tag,
        passes_bought
    ) {
        this.id = id;
        this.title_tag = title_tag;
        this.venue_tag = venue_tag;
        this.play_day = play_day;
        this.curtain_time =curtain_time;
        this.account_tag =account_tag;
        this.passes_bought =passes_bought;
    }
}