FROM python:3.9

RUN mkdir -p /app/app

COPY ./requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

EXPOSE 8000

WORKDIR /app/app

COPY ./app .

CMD ["python3", "-u", "main.py"]