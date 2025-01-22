FROM python:3.10-slim

RUN apt-get update && apt-get install -y tor
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

CMD service tor start && python app.py
