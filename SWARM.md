# SUBSCRIPTION SERVICE DOCKER SWARM GUIDE

---

!! Make sure you have some experience of working with docker-swarm before reading this guide.
Recommend to check this resources first: 

#### habr: [Docker-Swarm Guide]("https://habr.com/")

#### tutorial: [Docker-Swarm-Tutorial]("https://habr.com/")

--- 

# Usage 

*Creating  Docker-Swarm Cluster*
#### 1: If You don't have a docker-swarm cluster firstly you need to set it up.
#### If You have some problems with that, go check this tutorial:
[Setting up docker-swarm cluster]("http://")

#### After that you need to connect to the worker node by executing 

```editorconfig
docker swarm join --token `token you obtained after cluster initialization`
```

---

*Creating Docker-Swarm Node Stack* 
#### 2.The next step is to create a stack for you node, where the application is going to be deployed.
#### It is `important` to call the service with `subscription_service` name.

```editorconfig
docker service create --name subscription_service scratch 
docker service update --label-add TAG=subscription_service
```
#### It created empty stack and now we are ready for deploy.

#### To make sure that it does work out. Run.
```editorconfig
    docker stack ls
```

#### It will respond with all existing stacks. You need to make sure that there is a stack with `subscription_service` name.


*Stack Issues*

#### If you made something wrong during the previous step you can actually remove them.

```editorconfig
    # go to the manager node. 
    docker service rm `name of the wrong service`
```

--- 

*Deploying Services*

#### After that we can finally deploy the application.
#### Firstly go to the main directory where `docker-compose.yaml` file is located.
#### Run

```editorconfig
    docker stack deploy subscription_service --compose-file ./docker-compose.yaml
```
#### Ta-da-ms!
#### Now you can check that your services is being deployed to the stack by executing.
```editorconfig
    docker services ls 
```
---
#### For more info about me you can check my Github: [My Profile]("https://github.com/LovePelmeni")
#### Linkedin: Find me by Email `kirklimushin@gmail.com`

#### For contributions: Email `kirklimushin@gmail.com`