# SUBSCRIPTION SERVICE DOCKER SWARM GUIDE

---

!! Make sure you have some experience of working with docker-swarm before reading this guide.
Recommend to check this resources first: 

#### habr: [Docker-Swarm Guide]("https://habr.com/")

#### tutorial: [Docker-Swarm-Tutorial]("https://habr.com/")

--- 

# Requirements: 

~ `Docker` - `1.3.9 or higher` 

~ `Docker-Compose` - `3.8 or higher`

~ `Two Virtual Machines` or `One` if you already have initialized Docker-Swarm Cluster.
If You still haven't set them up. There is a guide for that: [Setting up Docker VM Machines.]("http://")


# Usage 

*Cloning Repo from the Source*

```editorconfig
    git clone https://github.com/LovePelmeni/SubscriptionService.git
```

### *Creating  Docker-Swarm Cluster*

---
#### 1: If You don't have a docker-swarm cluster firstly you need to set it up.
#### If You have some problems with that, go check this tutorial: [Setting up docker-swarm cluster]("http://")



### *Initializing Nodes for cluster*

---
#### After that initialize your manager node by executing following.. 
(If you already have a cluster and you already connected to it, you does not need to do it.)

#### *To get your cluster token, execute...*

```editorconfig
    $ docker swarm join-token worker
```

#### *After that, run:*

```editorconfig
    $ docker swarm --join `token that you obtained after cluster initialization`
```

--- 

#### *After that you need to connect to the worker node by executing*

```editorconfig
    $ docker swarm join --token `token you obtained after cluster initialization`
```

---

### *Deploying Services*

#### After that we can finally deploy the application.
#### Firstly go to the main directory where `docker-compose.yaml` file is located.
#### Run

```editorconfig
    docker stack deploy subscription_service --compose-file ./docker-compose.yaml
    docker service update --label-add TAG=subscription_service subscription_service
```
#### Ta-da-ms!
#### Now you can check that your services is being deployed to the stack by executing.
```editorconfig
    docker services ls 
```
---
#### For more info about me you can check my Github: ~ [My Profile]("https://github.com/LovePelmeni")

---

### *External Links*


#### ~ *LinkedIn*: Find me by Email `kirklimushin@gmail.com`

#### ~ *For contributions*: Email `kirklimushin@gmail.com`
