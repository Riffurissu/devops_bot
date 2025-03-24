FROM ubuntu:24.04
ENV TZ=Europe/Moscow
ENV PATH="/usr/bin:/bin:$PATH"
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update -y
RUN apt-get install -y coreutils
RUN apt-get install -y ssh
RUN apt-get install -y postgresql-16 postgresql-contrib
COPY ./pg_hba.conf /etc/postgresql/16/main/
COPY ./postgresql.conf /etc/postgresql/16/main/
RUN chown -R postgres:postgres /etc/postgresql/16/main
RUN service postgresql start
RUN service ssh start
COPY ./start.sh /start.sh
RUN chmod +x /start.sh
COPY ./init.sql /init.sql
RUN chmod 777 /init.sql
RUN echo postgres:tgbot | /usr/sbin/chpasswd
EXPOSE 5432
EXPOSE 22
CMD ["sh", "/start.sh"]
