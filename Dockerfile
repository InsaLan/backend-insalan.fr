FROM alpine:latest

EXPOSE 8080
WORKDIR /app

RUN apk add --no-cache python3 py3-pip postgresql15-dev gcc python3-dev musl-dev

COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

RUN cat .pgpass

COPY . /app/

CMD python manage.py runserver
