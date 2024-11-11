FROM python:3.13-slim

ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]