FROM ubuntu:16.04

MAINTAINER SALAR

RUN apt-get update
RUN apt-get install -y bc g++ python2.7 python3.5

RUN mkdir /var/judge

ADD ./scripts/main.sh /var/judge
RUN chmod a+x /var/judge/main.sh

WORKDIR /var/judge

CMD ["/bin/bash", "main.sh"]
