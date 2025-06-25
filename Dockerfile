FROM python:3.10 as base

WORKDIR /app
COPY . /app
COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

EXPOSE 9554
EXPOSE 123456

WORKDIR /app

CMD ["python","/app/main.py"]