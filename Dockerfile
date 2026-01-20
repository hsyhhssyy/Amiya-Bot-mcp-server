FROM python:3.12-slim

RUN useradd -m amiya

WORKDIR /app

RUN mkdir -p /app/resources

RUN apt-get update

RUN apt-get install -y --no-install-recommends \
    git \
    build-essential


ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

RUN python -m pip install --no-cache-dir playwright==1.57.0

RUN python -m playwright install --with-deps

RUN chmod -R 755 /ms-playwright
RUN chown -R amiya:amiya /ms-playwright

# 浏览器测试
RUN python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(); print('ok'); b.close(); p.stop()"

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

USER amiya

CMD ["python", "main.py"]
