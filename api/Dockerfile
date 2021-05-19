FROM python:3.9

WORKDIR /app

COPY ./requirements.txt .

RUN pip install -r ./requirements.txt

EXPOSE 8000

COPY ./app/ .

CMD ["python3", "-u", "main.py"]