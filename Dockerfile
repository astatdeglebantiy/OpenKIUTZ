FROM python:3.14-alpine

WORKDIR /app

RUN pip install --no-cache-dir pyyaml

COPY . .

EXPOSE 3000

CMD ["python", "-u", "main.py"]