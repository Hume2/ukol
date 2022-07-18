FROM python:3

ADD requirements.txt /

RUN pip install -r requirements.txt

ADD ukol.py /

ENTRYPOINT [ "python3", "./ukol.py" ]

EXPOSE 5432
