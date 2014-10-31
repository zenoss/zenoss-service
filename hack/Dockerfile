FROM ubuntu:trusty
MAINTAINER Zenoss, Inc <dev@zenoss.com>	

RUN	apt-get update -qq

# build dependencies
RUN	apt-get install -y -q make ruby ruby-dev rpm curl
RUN	gem install fpm

