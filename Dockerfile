FROM python:3.9-alpine
WORKDIR /app

ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0
ENV FLASK_APP app.py

EXPOSE 5001

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY . /app

CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5001"]
