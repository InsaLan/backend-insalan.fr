FROM python:3.9-alpine

EXPOSE 8000
WORKDIR /app

RUN apk add --no-cache postgresql15-dev gcc musl-dev

COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

COPY . /app/

ENTRYPOINT ["./entrypoint.sh"]
