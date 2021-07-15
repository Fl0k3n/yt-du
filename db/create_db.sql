CREATE TABLE IF NOT EXISTS playlists (
        ID SERIAL PRIMARY KEY,
        name text NOT NULL,
        url text UNIQUE NOT NULL,
        directory_path text UNIQUE NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        finished boolean NOT NULL
    );

CREATE TABLE IF NOT EXISTS playlist_links (
    ID SERIAL PRIMARY KEY,
    url text NOT NULL,
    title text NOT NULL,
    playlist_ID INT NOT NULL,
    cleaned_up boolean,
    FOREIGN KEY (playlist_ID)
        REFERENCES  playlists (ID)
);


CREATE TABLE IF NOT EXISTS data_links (
    ID SERIAL PRIMARY KEY,
    pl_link_ID INT NOT NULL,
    type VARCHAR(50),
    size INT,
    path text NOT NULL,
    downloaded INT NOT NULL DEFAULT 0,
    download_start_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (pl_link_ID)
        REFERENCES playlist_links(ID)
);


CREATE TABLE IF NOT EXISTS download_error_log (
    ID SERIAL PRIMARY KEY,
    data_link_ID INT NOT NULL,
    log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    msg text NOT NULL,
    FOREIGN KEY (data_link_ID)
        REFERENCES data_links(ID)
);

CREATE TABLE IF NOT EXISTS merge_status (
    ID SERIAL PRIMARY KEY,
    name text
);


CREATE TABLE IF NOT EXISTS merge_data (
    ID SERIAL PRIMARY KEY,
    pl_link_ID INT NOT NULL,
    status_ID INT NOT NULL DEFAULT 0,
    proc_exit_code INT,
    start_time TIMESTAMP,
    FOREIGN KEY (pl_link_ID)
        REFERENCES playlist_links(ID),
    FOREIGN KEY (status_ID)
        REFERENCES merge_status(ID)
);


CREATE TABLE IF NOT EXISTS merge_error_log (
    ID SERIAL PRIMARY KEY,
    log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    msg text NOT NULL,
    merge_ID INT NOT NULL,
    FOREIGN KEY (merge_ID)
        REFERENCES merge_data (ID)
);