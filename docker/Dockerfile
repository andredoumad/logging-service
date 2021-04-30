# https://hub.docker.com

FROM python:3.8

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir /server
WORKDIR /server
COPY ./server /server

RUN adduser user
USER user

