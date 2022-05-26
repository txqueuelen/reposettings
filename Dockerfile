FROM python:alpine

RUN mkdir /reposettings
WORKDIR /reposettings

RUN apk add build-base libffi-dev py3-pip py3-setuptools
COPY requirements.txt reposettings.py docker_entrypoint.sh ./
RUN pip install -r requirements.txt

ENTRYPOINT /reposettings/docker_entrypoint.sh
