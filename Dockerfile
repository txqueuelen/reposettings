FROM python:latest

RUN mkdir /reposettings
WORKDIR /reposettings

COPY requirements.txt reposettings.py docker_entrypoint.sh ./
RUN pip install -r requirements.txt

ENTRYPOINT /reposettings/docker_entrypoint.sh
