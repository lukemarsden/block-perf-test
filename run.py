"""
Starts mysql containers on a set of volumes: /big/[b-z], wiping them out first,
and running mysql_install_db.

Usage: run.py <number-of-containers>
"""

import os, sys

print 'disabling security'
os.system("setenforce 0")
# kill all containers
print 'killing containers...'
os.system("docker rm -f $(docker ps -a -q)")

print 'starting up', sys.argv[1], 'of them...'
for i in range(ord('b'), ord('b') + int(sys.argv[1])):
    x = chr(i)
    print 'doing', x
    path = "/big/%s" % (x,)
    hostPort = 4000 + i
    print 'allocating hostPort', hostPort
    os.system("rm -rf %s/*" % (path,))
    os.system("docker run -v %s:/var/lib/mysql dockerfile/percona mysql_install_db" % (path,))
    os.system("docker run -d -v %s:/var/lib/mysql --publish=%d:3306 --name=mysql-%d-%s dockerfile/percona" % (path, hostPort, i, x))
