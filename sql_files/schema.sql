CREATE TABLE IF NOT EXISTS players(
    puuid TEXT PRIMARY KEY NOT NULL,
    game_name TEXT,
    tag_line  TEXT,
    region   TEXT,
    profile_icon_id INT,
    revision_date TIMESTAMP,
    last_synced_at TIMESTAMP
);
CREATE TYPE ChallengePointDto AS(
    level TEXT,
    current BIGINT,
    max BIGINT,
    percentile REAL
                             );
CREATE TABLE IF NOT EXISTS player_snapshots(
     puuid TEXT NOT NULL,
     snapshot_date DATE NOT NULL,

     summoner_level INT,
     title TEXT,

     crest_border TEXT,
     banner_accent TEXT,
     prestige_crest_border_level INT,

     total_points ChallengePointDto,

     PRIMARY KEY(puuid, snapshot_date),
     FOREIGN KEY(puuid) REFERENCES players(puuid) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS masteries(
    puuid TEXT NOT NULL,
    champion_id BIGINT NOT NULL,

    champion_points_until_next_level INT,
    chest_granted BOOLEAN,
    last_play_time TIMESTAMP,
    champion_level INT,
    champion_points INT,
    champion_points_since_last_level INT,
    mark_required_for_next_level INT,
    champion_season_milestone INT,
    tokens_earned INT,
    milestone_grades TEXT[],

    PRIMARY KEY (puuid, champion_id),
    FOREIGN KEY (puuid) REFERENCES players (puuid) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS challenges(
    puuid TEXT NOT NULL,
    challenge_id BIGINT NOT NULL,

    percentile REAL,
    players_in_level INT,
    achieved_time TIMESTAMP,
    value REAL,
    level TEXT,
    position INT,

    PRIMARY KEY(puuid, challenge_id),
    FOREIGN KEY(puuid) REFERENCES players (puuid) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ranks(
    puuid TEXT NOT NULL,
    queue_type TEXT NOT NULL,
    snapshot_date DATE NOT NULL,

    tier TEXT,
    rank TEXT,
    league_points INT,
    wins INT,
    losses INT,
    hot_streak BOOLEAN,
    veteran BOOLEAN,
    fresh_blood BOOLEAN,
    inactive BOOLEAN,

    PRIMARY KEY(puuid, queue_type, snapshot_date),
    FOREIGN KEY(puuid, snapshot_date) REFERENCES player_snapshots(puuid, snapshot_date) ON DELETE CASCADE
)