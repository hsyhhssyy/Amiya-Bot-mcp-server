FROM python:3.12-slim

WORKDIR /app

RUN mkdir -p /app/resources

RUN apt-get update

RUN apt-get install -y --no-install-recommends \
    git \
    build-essential

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m pip install playwright==1.57.0

RUN python -m playwright install --with-deps chromium

CMD ["python", "main.py"]
