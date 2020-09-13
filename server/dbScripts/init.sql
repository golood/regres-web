DO LANGUAGE plpgsql
  $$
BEGIN
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

CREATE SEQUENCE tasks_id_seq START 1;
create table tasks (
  id                     bigint NOT NULL PRIMARY KEY DEFAULT nextval('tasks_id_seq'),
  type                   text
);

CREATE SEQUENCE worker_id_seq START 1;
create table worker (
  id                     bigint NOT NULL PRIMARY KEY DEFAULT nextval('worker_id_seq'),
  name                   text,
  time_start             timestamp,
  time_end               timestamp,
  count                  decimal,
  status                 text,
  user_id                bigint NOT NULL REFERENCES user_session (id),
  task_id                bigint REFERENCES tasks (id)
);

CREATE SEQUENCE result_id_seq START 1;
create table result (
  id                     bigint NOT NULL PRIMARY KEY DEFAULT nextval('result_id_seq'),
  alfa                   text,
  epselon                text,
  E                      text,
  bias_estimates         text,
  n1                     text,
  n2                     text
);


create table tasks_to_resalt (
  id_tasks               bigint NOT NULL REFERENCES tasks (id),
  id_result              bigint NOT NULL REFERENCES result (id)
);

create table blocker (
  id                     bigint NOT NULL PRIMARY KEY,
  limit_worker           bigint NOT NULL DEFAULT 1,
  run_worker             bigint NOT NULL DEFAULT 0
);
INSERT INTO blocker (id) VALUES (0);


create table service_list (
  id                     bigint NOT NULL PRIMARY KEY,
  launch                 boolean NOT NULL,
  last_active            timestamp
);

CREATE SEQUENCE queue_task_id_seq START 1;
CREATE SEQUENCE page_id_seq START 1;
create table queue_task (
  id                     bigint NOT NULL PRIMARY KEY DEFAULT nextval('queue_task_id_seq'),
  page                   bigint NOT NULL,
  service_id             bigint NOT NULL REFERENCES service_list (id),
  complete               boolean NOT NULL,
  task                   text NOT NULL,
  task_id                bigint,
  parcent                decimal
);
END$$;
