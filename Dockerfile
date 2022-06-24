FROM python:3.8.13-buster
MAINTAINER Klimushin Kirill kirklimushin@gmail.com

CMD mkdir /sub/app/
WORKDIR /sub/app/

ENV PYTHONUNBUFFERED=1
RUN echo "Running Docker Service Application Image 🍺. Project is created by < Klimushin Kirill > Email kirklimushin@gmail.com It will took some time. "

RUN pip install --upgrade pip
RUN pip freeze > requirements.txt
ADD ./requirements.txt ./requirements.txt
COPY . .

RUN pip install -r requirements.txt && \
RUN pip uninstall psycopg2-binary && pip install psycopg2-binary --no-cache-dir --no-input && \
RUN pip install backports-zoneinfo && \
RUN pip install gunicorn

RUN chmod +x ./subscription-entrypoint.sh
ENTRYPOINT ["sh", "./subscription-entrypoint.sh"]
