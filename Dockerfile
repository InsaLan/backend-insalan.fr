FROM python:3.12-alpine3.19

EXPOSE 8000
WORKDIR /app

RUN apk add --no-cache postgresql15-dev gcc musl-dev

COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

COPY . /app/

ENTRYPOINT ["./entrypoint.sh"]
