FROM       ubuntu:trusty
MAINTAINER Zenoss, Inc. <dev@zenoss.com>

RUN apt-get update && \
    apt-get -y install curl rpm2cpio && \
    cd /tmp && \
    curl -s http://artifacts.zenoss.loc/europa/serviced/2113/serviced-1.0.0_2113-1.x86_64.rpm | rpm2cpio | cpio -div && \
    mv opt/serviced/bin/serviced /usr/local/bin/serviced && \
    apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/ && \
    cd / && rm -rf /tmp/*

CMD ["/usr/local/bin/serviced", "template", "compile", "/usr/src/template"]