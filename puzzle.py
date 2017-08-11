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

def isodd(num):
    return num & 1

if isodd(args.cellsw) or isodd(args.cellsh):
    print("Warning, odd cell numbers make some corners obvious.")

dwg = svgwrite.Drawing(outputname)

stroke = svgwrite.rgb(0,0,0)
#stroke = svgwrite.rgb(0,0,0)

blobw = onecellw / 8.0
blobh = onecellh / 8.0

random.seed(0)

def cellcentre(x, y):
    return (x+0.5)*onecellw, (y+0.5)*onecellh

def blob_start(direction, cellcentre, invert=False):
    toedgeh = (onecellh/2)
    toedgew = (onecellw/2)
    if invert:
        offseth = toedgeh - (blobh*1.25)
        offsetw = toedgew - (blobw*1.25)
    else:
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
    dist = (random.random()/6) + (5/12)
    width = random.random()/8 + (1/6)
    return dist, width

def dist_between(ia, ib):
    return math.sqrt(sum((a-b)**2) for a, b in zip(ia, ib))

def partial_line(start, end, dist, onto=None):
    if onto is None:
        onto = start
    return tuple((o + ((e-s)*dist)) for o, s, e in zip(onto, start, end))

def edge_line(dwg, centre, startpoint, endpoint, blobdir, flat=False):
    path = dwg.path(stroke=stroke, fill="none")
    path.push("M", *startpoint)
    if not flat:
        dist, width = connector_nums()
        connector_start = dist - (width/2)
        connector_end = dist + (width/2)
        path.push("L", *partial_line(startpoint, endpoint, connector_start))

        inv = random.choice([True, False])
        blob_s = blob_start(blobdir, centre, invert=inv)

        conn_1 = partial_line(startpoint, endpoint, connector_start-width/2, onto=blob_s)
        conn_2 = partial_line(startpoint, endpoint, connector_end+width/2, onto=blob_s)
        path.push("L", *conn_1)
        path.push("L", *conn_2)
    
        path.push("L", *partial_line(startpoint, endpoint, connector_end))

    path.push("L", *endpoint)
    dwg.add(path)

for x, y in itertools.product(range(args.cellsw), range(args.cellsh)):
    #print("%d, %d" % (x,y))
    xmm = x * onecellw
    ymm = y * onecellh

    topleft = xmm, ymm
    bottomright = xmm + onecellw, ymm + onecellh
    topright = bottomright[0], topleft[1]
    bottomleft = topleft[0], bottomright[1]

    centre = cellcentre(x, y)

    if x == 0:
        edge_line(dwg, centre, topleft, bottomleft, 'left', flat=True)
    if y == 0:
        edge_line(dwg, centre, topleft, topright, 'up', flat=True)

    flat_right = x==args.cellsw-1 or (y in[0,args.cellsh-1] and x%2==1)
    flat_bottom = y==args.cellsh-1 or (x in[0, args.cellsw-1] and y%2==1)
    edge_line(dwg, centre, topright, bottomright, 'right', flat=flat_right)
    edge_line(dwg, centre, bottomleft, bottomright, 'down', flat=flat_bottom)

dwg.save()
