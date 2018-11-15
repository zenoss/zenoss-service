FROM ubuntu:xenial
MAINTAINER Zenoss, Inc <dev@zenoss.com>	

# build dependencies
RUN	apt-get update -qq && apt-get install -y -q build-essential libtool rpm curl make autoconf ruby ruby-dev
RUN	gem install --no-ri --no-rdoc fpm

