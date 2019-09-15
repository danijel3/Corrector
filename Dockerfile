FROM python:3.7-alpine

COPY requirements.txt /tmp/

RUN apk add --virtual build-dependencies --update gcc g++ python3-dev libffi-dev && \
    pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir flask gunicorn && \
    pip3 install --no-cache-dir -r /tmp/requirements.txt && \
    rm -rf /tmp/requirements.txt && \
    apk del build-dependencies

WORKDIR /app

RUN head -c 24 /dev/urandom | base64 > /app/secret

COPY static /app/static/
COPY templates /app/templates/
COPY *.py /app/

EXPOSE 80

CMD gunicorn --bind 0.0.0.0:80 --timeout=1800 --workers=4 --threads=4 --max-requests=30 --max-requests-jitter=20 --name=gunicorn  wsgi