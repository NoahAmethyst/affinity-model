FROM python:3.10 as base

WORKDIR /app
COPY . /.
COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

EXPOSE 9554

WORKDIR /app

CMD ["python","main.py"]