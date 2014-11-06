FROM ubuntu:trusty
MAINTAINER Zenoss, Inc <dev@zenoss.com>	

# build dependencies
RUN	apt-get update -qq && apt-get install -y -q make ruby ruby-dev rpm curl
RUN	gem install fpm

