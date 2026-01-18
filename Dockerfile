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

RUN playwright install chromium

RUN python -m pip show playwright
RUN python -c "import sys; print('\n'.join(sys.path))"

RUN python -m playwright install --with-deps

CMD ["python", "main.py"]
