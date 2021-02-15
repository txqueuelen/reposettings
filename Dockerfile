FROM alpine:latest

RUN apk add python3 py3-pip py3-setuptools
RUN mkdir /reposettings
WORKDIR /reposettings

COPY requirements.txt reposettings.py docker_entrypoint.sh ./
RUN pip install -r requirements.txt

ENTRYPOINT /reposettings/docker_entrypoint.sh
