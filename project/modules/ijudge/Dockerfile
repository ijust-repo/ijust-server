FROM ubuntu:16.04

MAINTAINER SALAR

RUN apt-get update
RUN apt-get install -y bc g++ python2.7 python3.5 default-jre default-jdk
RUN apt-add-repository ppa:webupd8team/java
RUN apt-get update && \
	echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections && \
	apt-get install -y oracle-java8-installer

RUN mkdir /var/judge

ADD ./scripts/main.sh /var/judge
RUN chmod a+x /var/judge/main.sh

WORKDIR /var/judge

CMD ["/bin/bash", "main.sh"]
