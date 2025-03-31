CREATE DATABASE db_bot_data;
\c db_bot_data;
CREATE TABLE emails (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL
);
CREATE TABLE phones (
    id SERIAL PRIMARY KEY,
    phone TEXT NOT NULL
);
INSERT INTO emails (email) VALUES ('test1@test.ru'), ('test2@test.ru');
INSERT INTO phones (phone) VALUES ('+71111111111'), ('82222222222');
CREATE ROLE repl_bot_user WITH LOGIN REPLICATION PASSWORD 'botrepl';
ALTER USER postgres WITH PASSWORD 'tgbot';
