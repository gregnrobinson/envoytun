FROM nginx

RUN apt update
RUN apt install iptables curl iputils-ping -y 