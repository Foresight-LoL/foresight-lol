create type test.challengepointdto as
(
    level      text,
    current    bigint,
    max        bigint,
    percentile real
);

alter type test.challengepointdto owner to dev;

create type test.test_dto as
(
    number integer
);

alter type test.test_dto owner to dev;

create table test.players
(
    puuid     text not null
        primary key,
    game_name text,
    tag_line  text,
    region    text,
    synced_at timestamp with time zone
);

alter table test.players
    owner to dev;

create table test.masteries
(
    puuid                            text   not null
        references test.players
            on delete cascade,
    champion_id                      bigint not null,
    champion_points_until_next_level integer,
    chest_granted                    boolean,
    last_play_time                   timestamp with time zone,
    champion_level                   integer,
    champion_points                  integer,
    champion_points_since_last_level integer,
    mark_required_for_next_level     integer,
    champion_season_milestone        integer,
    tokens_earned                    integer,
    milestone_grades                 text[],
    primary key (puuid, champion_id)
);

alter table test.masteries
    owner to dev;

create table test.challenges
(
    puuid            text   not null
        references test.players
            on delete cascade,
    challenge_id     bigint not null,
    percentile       real,
    players_in_level integer,
    achieved_time    timestamp with time zone,
    value            real,
    level            text,
    position         integer,
    primary key (puuid, challenge_id)
);

alter table test.challenges
    owner to dev;

create table test.player_snapshots
(
    puuid                       text not null
        references test.players
            on delete cascade,
    snapshot_date               date not null,
    summoner_level              integer,
    title                       text,
    profile_icon_id             integer,
    crest_border                text,
    banner_accent               text,
    prestige_crest_border_level integer,
    total_points                test.challengepointdto,
    primary key (puuid, snapshot_date)
);

alter table test.player_snapshots
    owner to dev;

create table test.rank_snapshots
(
    puuid         text                     not null
        references test.players
            on delete cascade,
    queue_type    text                     not null,
    snapshot_time timestamp with time zone not null,
    tier          text,
    rank          text,
    league_points integer,
    wins          integer,
    losses        integer,
    hot_streak    boolean,
    veteran       boolean,
    fresh_blood   boolean,
    inactive      boolean,
    primary key (puuid, queue_type, snapshot_time)
);

alter table test.rank_snapshots
    owner to dev;

create table test.test_table
(
    id       integer not null
        primary key,
    dto_test test.test_dto
);

alter table test.test_table
    owner to dev;

