CREATE SEQUENCE user_session_id_seq START 1;
create table user_session (
    id                   bigint NOT NULL PRIMARY KEY default nextval('user_session_id_seq'),
    session_id           text NOT NULL,
    date_create          timestamp NOT NULL,
    date_last_active     timestamp NOT NULL,
    ip_adress            text
);



CREATE SEQUENCE files_id_seq START 1;
create table load_files (
    id                   bigint NOT NULL PRIMARY KEY default nextval('files_id_seq'),
    user_id              bigint NOT NULL REFERENCES user_session (id),
    file_name            text NOT NULL
);

CREATE SEQUENCE matrix_id_seq START 1;
create table matrix (
  id                     bigint NOT NULL,
  row_id                 bigint NOT NULL,
  column_id              bigint NOT NULL,
  value                  text NOT NULL
);
