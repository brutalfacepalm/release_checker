FROM python:3.10

RUN apt-get update
RUN mkdir -p /fastapi
WORKDIR /fastapi

COPY . /fastapi

RUN pip install --no-cache-dir --upgrade -r /fastapi/requirements.txt

RUN apt-get install -y curl
RUN chmod -R 777 /fastapi