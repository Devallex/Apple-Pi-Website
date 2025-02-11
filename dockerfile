FROM python

COPY . /app
WORKDIR  /app

RUN pip3 install -r requirements.txt

CMD python3 project