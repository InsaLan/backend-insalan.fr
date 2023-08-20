\set user_name `echo ${DB_USER}`
\set test_user `echo ${DB_USER}_test`
\set user_pass `echo ${DB_PASS}`
\set db_name `echo ${DB_NAME}`

CREATE USER :test_user WITH PASSWORD :'user_pass';
ALTER USER :test_user CREATEDB;

CREATE USER :user_name WITH PASSWORD :'user_pass';
CREATE DATABASE :db_name;
GRANT ALL ON DATABASE :db_name TO :user_name;
\c :db_name
GRANT USAGE, CREATE ON SCHEMA public TO :user_name;

