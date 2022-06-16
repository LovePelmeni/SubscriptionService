
# Subscription Service

Docs Link: [API Documentation]("http://localhost:8077/swagger/")

`Subscription Service`
`Date: 24.05.22`


### Short Introduction:

App allows creating custom subscriptions and apply them on specific period of time. default by `month`.
Also gives the catalog subs, applied subs, expiration checker and cancellation.
### Technologies used in the project:

```ini

[multiprocessing libraries] 
Celery 

[Message Brokers]
RabbitMQ 

[Databases]
Redis, PostgresSQL, MongoDB

[Frameworks]
Django

```

### Dependencies:
    
### `python`  3.8 
### `postgresql`: 14.0
### `mongoDB`: latest (up to the date "26.05.22")
### `rabbitMQ`: latest (up to the date "26.05.22")
### `nginx`: latest (up to the date "26.05.22")

### Operational System: tested on macOS and Linux-Ubuntu (18.04.03).
### Not recommended to use Windows.

# Usage

`1: Make Sure Matching of the dependencies.`

Copy repository:
    
```doctest
    git clone http://github.com/LovePelmeni/SubscriptionService.git
```


### *For Production environment*

---

1: Check the `project/sub_env.env` file and `set env variables` for the project to start.


---
#### If Running separately as integration.
2: Go to the `Analytic/separate_start` directory of the project and start docker-compose.yaml with:

```doctest
    docker-compose up -d 
```
---
#### If Running with other services.

1: Check If Network with name `global_application_network` exists.
(I'm about docker network). It is necessary for communication between applications.


2: Go to the `Analytic/project` directory of the project and start docker-compose.yaml with:

```doctest
    docker-compose up -d 
```
---


### *For Local Environment* 

---
1. Go to `Analytic/Analytic/settings.py` and replace `DEBUG` with `True`.
2.    ...
```doctest

    $ ~ python manage.py makemigrations --database backup_database 
    
    $ ~ python manage.py migrate


    $ ~ python manage.py makemigrations --database default # name of the main database in settings.py file at DATABASES const.
    
    $ ~ python manage.py migrate

    $ ~ python manage.py runserver

```



Tip: `On Exception Highly Recommend rebuilding the application.`


### Go check UI-Documentation by clicking at `API Docs` button at the top.
