FROM ubuntu:20.04

RUN apt update
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata
RUN apt install -y python3-pip firefox-geckodriver
RUN apt install -y libpq5 libpq-dev
ADD requirements.txt /

RUN pip install -r requirements.txt

ADD ukol.py /

ENTRYPOINT [ "python3", "./ukol.py" ]

EXPOSE 8080
