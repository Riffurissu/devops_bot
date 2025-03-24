#/bin/bash
service postgresql start
until pg_isready -U postgres; do
	echo "Waiting for PostgreSQL to start..."
	sleep 2
done
psql -U postgres -f /init.sql
service ssh start
while true; do sleep 1; done
