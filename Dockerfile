FROM python:3.8.1-alpine

ENV DIGITALOCEAN_ACCESS_TOKEN ""

WORKDIR /home/do

COPY ./requirements.txt ./
COPY ./digitalocean_snapshooter.py ./

RUN pip install -r requirements.txt

ENTRYPOINT ["/home/do/digitalocean_snapshooter.py"]
CMD ["--help"]
