FROM python:3.12-alpine

WORKDIR /app

RUN pip install --no-cache-dir pyyaml

COPY core/ ./core/
COPY server/ ./server/
COPY templates/ ./templates/
COPY static/ ./static/
COPY inwards/ ./inwards/
COPY schedules/ ./schedules/
COPY config.py config.yaml groups.yaml main.py ./

RUN mkdir -p resources

EXPOSE 3000

CMD ["python", "-u", "main.py"]