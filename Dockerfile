# syntax=docker/dockerfile:1
FROM python:3.12.4-slim-bullseye
RUN pip install requests python-dotenv
WORKDIR /usr/src/app
COPY app .
CMD ["python", "-u", "app.py"]