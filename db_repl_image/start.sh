#/bin/bash
service postgresql stop
rm -rf /var/lib/postgresql/16/main/*
pg_basebackup -R -h pg_server -U repl_bot_user -D /var/lib/postgresql/16/main/ -P
chmod -R 777 /var/lib/postgresql/16/main/*
chmod 777 /var/lib/postgresql/16/main/PG_VERSION
service postgresql start
while true; do sleep 1; done
