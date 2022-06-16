FROM python:3.8.13-buster
MAINTAINER Klimushin Kirill kirklimushin@gmail.com

WORKDIR sub/app/
RUN pip install --upgrade pip
ENV PYTHONUNBUFFERED=1

COPY ./project/prod_requirements.txt prod_requirements.txt
RUN pip install psycopg2 --no-cache-dir --no-input
RUN pip install backports-zoneinfo
RUN pip install gunicorn

RUN pip install -r prod_requirements.txt
COPY . .

RUN chmod +x ./subscription-entrypoint.sh
ENTRYPOINT ["sh", "./subscription-entrypoint.sh"]


