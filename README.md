    
# Subscription Service

Docs Link: [API Documentation]("http://localhost:8077/swagger/")

`Subscription Service`
`Date: 24.05.22`


###Technologies used in the project:

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


###Short Introduction:

So the project consists of `Main Django Application` that is sort of 
separated service. It uses `MongoDB` as a `Subscription Document Storage`.
That Allows to obtain tons of them in a really short period of time. 
`PostgresSQL` as a database for more structured data.


### Dependencies:
    
### `python`  3.8 
### `postgresql`: 14.0
### `mongoDB`: latest (up to the date "26.05.22")
### `rabbitMQ`: latest (up to the date "26.05.22")
### `nginx`: latest (up to the date "26.05.22")

# Usage
    
`1: Make Sure Matching of the dependencies.`

Copy repository:
    
git clone ``

1: Check the project/sub_env.env file in order to check that there is no conflicts.

2: Check If Network with name `global_application_network` exists.
(I'm about docker network). It is necessary for communication between applications.


Run docker-compose.yaml file in the main directory:

```yaml
  docker-compose up -d 
```

Tip: `On Exception Highly Recommend rebuilding the application.`


`Go check UI-Documentation by following url`: "http://localhost:8077/swagger/".




