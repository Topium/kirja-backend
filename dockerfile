FROM python:3.8.20-bullseye

RUN groupadd -r uwsgi && useradd -r -g uwsgi uwsgi

COPY ./dev-requirements.txt /app/requirements.txt
COPY ./config.py /app/config.py
COPY ./server.py /app/server.py
COPY ./books.py /app/books.py
COPY ./utils.py /app/utils.py
WORKDIR /app
ENV SCRIPT_NAME=/testapp

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

EXPOSE 8080
USER uwsgi

CMD [ "uwsgi", "--http", ":8080", "--wsgi-file", "server.py", "--callable", "app", "--mount", "/books-api=server.py", "--manage-script-name" ]
