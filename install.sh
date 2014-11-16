#!/usr/bin/bash

yum install -y bzr
bzr branch lp:~percona-dev/perconatools/tpcc-mysql
yum install -y gnuplot

yum install -y docker
service docker start

yum install -y http://www.percona.com/downloads/percona-release/redhat/0.1-3/percona-release-0.1-3.noarch.rpm
yum install -y Percona-Server-client-56.x86_64
yum install -y Percona-Server-devel-56.x86_64

yum group install -y "Development Tools"
yum install -y openssl-devel
cd tpcc-mysql/src; make

yum install -y wget
cd /tmp; wget https://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-2.noarch.rpm; yum install -y epel-release-7-2.noarch.rpm
yum install -y python-pip
yum install -y python-devel
pip install twisted
