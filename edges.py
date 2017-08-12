#!/usr/bin/env python
import argparse
import itertools
import cv2


parser = argparse.ArgumentParser()
parser.add_argument("image")
parser.add_argument("--t1", required=True, type=int)
parser.add_argument("--t2", required=True, type=int)
args = parser.parse_args()

baseimage = cv2.imread(args.image, 0)

canny1 = args.t1
canny2 = args.t2

edgeimage = cv2.Canny(baseimage, canny1, canny2)

edge_file_name = args.image + "_edges.png"

cv2.imwrite(edge_file_name, edgeimage)
