#!/usr/bin/env python
import argparse
import itertools
import cv2


parser = argparse.ArgumentParser(description="Test image edge detection thresholds")
parser.add_argument("image", help="Input image file")
parser.add_argument("--t1", required=True, type=int, help="Threshold 1")
parser.add_argument("--t2", required=True, type=int, help="Threshold 2")
args = parser.parse_args()

baseimage = cv2.imread(args.image, 0)

canny1 = args.t1
canny2 = args.t2

edgeimage = cv2.Canny(baseimage, canny1, canny2)

edge_file_name = args.image + "_edges.png"

cv2.imwrite(edge_file_name, edgeimage)
