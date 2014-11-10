"""
Starts mysql containers on a set of volumes: /big/[b-z], wiping them out first,
and running mysql_install_db.

Usage: run.py <number-of-containers>
"""

import os, sys

# kill all containers
os.system("docker rm -f $(docker ps -a -q)")

# ord('z')

for i in range(ord('b'), ord('b') + int(sys.argv[1])):
    x = chr(i)
    print 'doing', x
    path = "/big/%s" % (x,)
    os.system("rm -rf %s/*" % (path,))
    os.system("docker run -v %s:/data dockerfile/percona mysql_install_db" % (path,))
    os.system("docker run -d -v %s:/data dockerfile/percona" % (path,))


