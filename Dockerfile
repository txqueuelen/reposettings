FROM python:3-slim

RUN apt update && \
    apt install -y git && \
    apt clean

RUN mkdir /reposettings
WORKDIR /reposettings
COPY requirements.txt reposettings.py docker_entrypoint.sh ./

RUN pip install -r requirements.txt

ENTRYPOINT /reposettings/docker_entrypoint.sh
