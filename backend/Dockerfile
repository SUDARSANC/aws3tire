FROM python:3.14-slim

WORKDIR /app

COPY app.py .

RUN pip install --no-cache-dir flask flask-cors mysql-connector-python werkzeug

EXPOSE 5000

CMD ["python", "app.py"]
