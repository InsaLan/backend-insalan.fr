FROM alpine:latest

EXPOSE 8000
WORKDIR /app

RUN apk add --no-cache python3 py3-pip postgresql15-dev gcc python3-dev musl-dev

COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

COPY . /app/

CMD ./entrypoint.sh
