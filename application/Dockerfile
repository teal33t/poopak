FROM python:3.6.1
MAINTAINER Y0LAT0 "yolato@protonmail.com"

COPY . /app
ENV HOME=/app
WORKDIR /app

RUN pip install -r requirements.txt

ADD docker_wait /wait
RUN chmod +x /wait
CMD /wait
