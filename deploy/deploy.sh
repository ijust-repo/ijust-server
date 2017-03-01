#! /bin/sh


docker build -f Dockerfile -t ijust_image ../
docker run -d --name ijust_container -p 443:80 ijust_image
