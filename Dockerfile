FROM python:3.12-alpine

WORKDIR /app

COPY core/ ./core/
COPY server/ ./server/
COPY templates/ ./templates/
COPY static/ ./static/
COPY config.py main.py ./

RUN mkdir -p inwards resources

EXPOSE 3000

CMD ["python", "-u", "main.py"]