#!/usr/bin/env python
import os
import math
import random
import svgwrite
from PIL import Image, ImageFilter
import argparse
import itertools
from scipy import misc as scipymisc
from skimage import color as skimagecolor, measure as skimagemeasure
from tempfile import mkdtemp
import cv2
import numpy as np
from scipy.stats import itemfreq


parser = argparse.ArgumentParser(description="Generate an evil jigsaw puzzle for laser cutting")
parser.add_argument("image" , help="Path to image file")
parser.add_argument("--widthmm", type=float, required=True, help="Width of resulting jigsaw (mm)")
parser.add_argument("--heightmm", type=float, required=True, help="Height of resulting jigsaw")
parser.add_argument("--cellsw", type=int, required=True, help="Number of jigsaw pieces in horizontal axis")
parser.add_argument("--cellsh", type=int, required=True, help="Number of jigsaw pieces in vertical axis")
parser.add_argument("--t1", required=True, type=int, help="Edge detection threshold 1 (use edges.py to help decide thresholdss quickly)")
parser.add_argument("--t2", required=True, type=int, help="Edge detection threshold 2")
parser.add_argument("--colours", default=3, type=int, help="Number of colours to use in final jigsaw (default=3)")

args = parser.parse_args()

# Load the image, get the size
baseimage = cv2.imread(args.image)
imgheight, imgwidth, _ = baseimage.shape
print(imgwidth)
print(imgheight)
print(args.widthmm)
print(args.heightmm)
scalew = args.widthmm/imgwidth
scaleh = args.heightmm/imgheight
print(scalew)
print(scaleh)
print(scalew*imgwidth)
print(scaleh*imgheight)

# Detect edges
edgeimage = cv2.Canny(baseimage, args.t1, args.t2)

# Get an instance of the image into scipy format
tempdir = mkdtemp()
tempfile = tempdir+ 'tempedge.png'
cv2.imwrite(tempfile, edgeimage)
fimg = scipymisc.imread(tempfile)
os.unlink(tempfile)
os.rmdir(tempdir)

outputname = args.image + ".svg"

onecellw = args.widthmm / args.cellsw
onecellh = args.heightmm / args.cellsh

def isodd(num):
    return num & 1

if isodd(args.cellsw) or isodd(args.cellsh):
    print("Warning, odd cell numbers make some corners obvious.")

dwg = svgwrite.Drawing(outputname, size=("%dmm" % (args.widthmm), "%dmm" % (args.heightmm)), viewBox='0, 0, %d, %d' % (args.widthmm, args.heightmm))

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

    imgtopleft = int(xmm / scalew), int(ymm / scaleh)
    imgbottomright = int(imgtopleft[0] + (onecellw / scalew)), int(imgtopleft[1] + (onecellh / scaleh))

    imgslice = baseimage[imgtopleft[1]:imgbottomright[1], imgtopleft[0]:imgbottomright[0]]

    arr = np.float32(imgslice)
    pixels = arr.reshape((-1, 3))

    n_colors = args.colours
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, .1)
    flags = cv2.KMEANS_RANDOM_CENTERS
    _, labels, centroids = cv2.kmeans(pixels, n_colors, None, criteria, 10, flags)

    palette = np.uint8(centroids)
    quantized = palette[labels.flatten()]
    quantized = quantized.reshape(imgslice.shape)

    dominant_colour = palette[np.argmax(itemfreq(labels)[:, -1])]
    #print(dominant_colour)

    centre = cellcentre(x, y)

    dwg.add(dwg.ellipse(centre, r=(onecellw/2.5, onecellw/2.5), fill="#%02x%02x%02x" % (
        dominant_colour[2],
        dominant_colour[1],
        dominant_colour[0]
    )))

    if x == 0:
        edge_line(dwg, centre, topleft, bottomleft, 'left', flat=True)
    if y == 0:
        edge_line(dwg, centre, topleft, topright, 'up', flat=True)

    flat_right = x==args.cellsw-1 or (y in[0,args.cellsh-1] and x%2==1)
    flat_bottom = y==args.cellsh-1 or (x in[0, args.cellsw-1] and y%2==1)
    edge_line(dwg, centre, topright, bottomright, 'right', flat=flat_right)
    edge_line(dwg, centre, bottomleft, bottomright, 'down', flat=flat_bottom)

gimg = skimagecolor.colorconv.rgb2grey(fimg)
contours = skimagemeasure.find_contours(gimg, 0.7)


for contour in contours:
    path = dwg.path(stroke="red", fill="none")
    first = True
    for y, x in contour:
        path.push("M" if first else "L", x*scalew, y*scaleh)
        first = False
    dwg.add(path)

dwg.save()

