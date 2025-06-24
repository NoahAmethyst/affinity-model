FROM python:3.10 as base

WORKDIR /app
COPY . /.
COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

EXPOSE 9554

WORKDIR /app

CMD ["python","main.py"]