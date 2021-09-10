FROM python:3

WORKDIR /root

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .

VOLUME .aws

ENTRYPOINT ["python"]
