#!/usr/bin/env python
import math
import random
import svgwrite
from PIL import Image
import argparse
import itertools

parser = argparse.ArgumentParser()
parser.add_argument("image")
parser.add_argument("--widthmm", type=float, required=True)
parser.add_argument("--heightmm", type=float, required=True)
parser.add_argument("--cellsw", type=int, required=True)
parser.add_argument("--cellsh", type=int, required=True)

args = parser.parse_args()

image = Image.open(args.image)

outputname = args.image + ".svg"

onecellw = args.widthmm / args.cellsw
onecellh = args.heightmm / args.cellsh

dwg = svgwrite.Drawing(outputname)

stroke = svgwrite.rgb(0,0,0)
#stroke = svgwrite.rgb(0,0,0)

blobw = onecellw / 8.0
blobh = onecellh / 8.0

random.seed(0)

def cellcentre(x, y):
    return (x+0.5)*onecellw, (y+0.5)*onecellh

def blob_start(direction, cellcentre):
    toedgeh = (onecellh/2)
    toedgew = (onecellw/2)
    offseth = toedgeh + (blobh*1.25)
    offsetw = toedgew + (blobw*1.25)

    if direction=='up':
        return cellcentre[0] - toedgew, cellcentre[1] - offseth
    if direction=='down':
        return cellcentre[0] - toedgew, cellcentre[1] + offseth
    if direction=='left':
        return cellcentre[0] - offsetw, cellcentre[1] - toedgeh
    if direction=='right':
        return cellcentre[0] + offsetw, cellcentre[1] - toedgeh

def connector_nums():
    #dist = (random.random()/4) + (3/8)
    dist = (random.random()/6) + (5/12)
    width = random.random()/8 + (1/6)
    return dist, width

def dist_between(ia, ib):
    return math.sqrt(sum((a-b)**2) for a, b in zip(ia, ib))

def partial_line(start, end, dist, onto=None):
    if onto is None:
        onto = start
    return tuple((o + ((e-s)*dist)) for o, s, e in zip(onto, start, end))

def edge_line(dwg, centre, startpoint, endpoint, blobdir):
    path = dwg.path(stroke=stroke, fill="none")
    path.push("M", *startpoint)
    dist, width = connector_nums()
    connector_start = dist - (width/2)
    connector_end = dist + (width/2)
    path.push("L", *partial_line(startpoint, endpoint, connector_start))

    blob_s = blob_start(blobdir, centre)

    conn_1 = partial_line(startpoint, endpoint, connector_start-width/2, onto=blob_s)
    conn_2 = partial_line(startpoint, endpoint, connector_end+width/2, onto=blob_s)
    path.push("L", *conn_1)
    path.push("L", *conn_2)
    
    path.push("L", *partial_line(startpoint, endpoint, connector_end))
    path.push("L", *endpoint)
    dwg.add(path)

for x, y in itertools.product(range(args.cellsw), range(args.cellsh)):
    print("%d, %d" % (x,y))
    xmm = x * onecellw
    ymm = y * onecellh

    topleft = xmm, ymm
    bottomright = xmm + onecellw, ymm + onecellh
    topright = bottomright[0], topleft[1]
    bottomleft = topleft[0], bottomright[1]

    centre = cellcentre(x, y)

    if x == 0:
        edge_line(dwg, centre, topleft, bottomleft, 'left')
    if y == 0:
        edge_line(dwg, centre, topleft, topright, 'up')
    edge_line(dwg, centre, topright, bottomright, 'right')
    edge_line(dwg, centre, bottomleft, bottomright, 'down')

dwg.save()
