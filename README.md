    
# Subscription Service

Docs Link: ('Docs')["http://localhost:8077/docs/"]

    SUBSCRIPTION SERVICE (EXTENSION FOR WEB APP) 

                Date: 24.05.22
I have finally released new API service for Web App Project.

Technologies used in the project:
    
    Celery, RabbitMQ, Redis, Django etc...


Short Introduction:

So the project consists of Main Django Application that is sort of 
separated service. It uses MongoDB as a Subscription Document Storage.
That Allows to obtain tons of them in a really short period of time. 
PostgresSQL as a database for more structured data.

# Technologies

##Databases
    
    PostgresSQL
    MongoDB 
    Redis

##Message Brokers
    
    RabbitMQ 

##Web Server
    
    Nginx 

##Language

    Python 

Dependencies:
    
    python: 3.8 
    postgresql: 14.0
    mongoDB: latest (up to the date "26.05.22")
    rabbitMQ: latest (up to the date "26.05.22")
    nginx: latest (up to the date "26.05.22")

#Usage
    
    1: Make Sure Matching of the dependencies.
    

Run Rabbitmq Docker-Compose File from "Services" Branch

    cd rabbitmq
    
    docker-compose up -d 

Copy repository:
    
    git clone <repository_name>

Install Docker Images:
    
    docker pull <sup_application>


1: Check the project/sub_env.env file in order to check that there is no conflicts.

2: Check If Network with name "global_application_network" exists.
(I'm about docker network). It is necessary for communication between applications.


Run docker-compose.yaml file in the main directory: 
    
    docker-compose up -d 

Tip: On Exception Highly Recommend rebuilding the application.


Go check UI-Documentation by following url: "http://localhost:8077/swagger/".




