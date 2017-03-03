#! /bin/sh

docker build -f Dockerfile -t ijust ../
docker-compose up -d
