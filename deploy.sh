#!/bin/bash

app=niesapi

# Cria a imagem do container: 
docker build -t docker.registry:5000/${app}-web .
docker push docker.registry:5000/$app-web

# Deploy do serviço, cria os containers / sobe a aplicação:
docker stack deploy -c ${app}.yml ${app}
