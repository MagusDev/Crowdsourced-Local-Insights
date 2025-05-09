FROM python:3.13-alpine
WORKDIR /app

RUN apk add --no-cache supervisor

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/db
RUN mkdir -p /app/instance/cache
RUN mkdir -p /etc/supervisor.d

COPY supervisord.conf /etc/supervisor.d/supervisord.ini

ENV FLASK_APP=geodata
EXPOSE 5000
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor.d/supervisord.ini"]