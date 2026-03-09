#!/bin/bash

apt update -y

apt install -y docker.io docker-compose git

systemctl start docker
systemctl enable docker

cd /home/ubuntu

git clone https://github.com/dovbeta/edim.git

cd edim

docker compose -f docker-compose.prod.yml up -d