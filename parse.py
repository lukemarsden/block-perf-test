#!/usr/bin/python
import os
paths = ["many-volumes-results", "single-volume-results"]
for p in paths:
    files = []
    for f in os.listdir(p):
        files.append(f)
    files.sort()
    for f in files:
        line = open("%s/%s" % (p, f), "r").read()
        chunks = line.split(" ")
        print p + ",",  f.split(".")[0].split("-")[5] + ",",
        for c in chunks:
            if 'n' in c:
                tpts = c.split('n')[0]
                print tpts + ",",
        print
