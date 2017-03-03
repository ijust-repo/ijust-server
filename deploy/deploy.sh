#! /bin/sh

docker build -f Dockerfile -t ijust_image ../
docker run -d --name ijust_container -v /var/www/ijust:/var/www/ijust -v /tmp:/tmp -h masterhost ijust_image
