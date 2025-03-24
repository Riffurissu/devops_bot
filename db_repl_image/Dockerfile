FROM ubuntu:24.04
ENV TZ=Europe/Moscow
ENV PATH="/usr/bin:/bin:$PATH"
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update -y
RUN apt-get install -y coreutils
RUN apt-get install -y postgresql-16 postgresql-contrib
RUN chown postgres:postgres /var/lib/postgresql/16/main/
EXPOSE 5432
COPY ./start.sh /start.sh
CMD ["sh", "/start.sh"]
