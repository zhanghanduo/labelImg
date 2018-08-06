#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
import os
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from lxml import etree
import codecs

TXT_EXT = '.txt'
ENCODE_METHOD = 'utf-8'


class YOLOWriter:

    def __init__(self, foldername, filename, imgSize, databaseSrc='Unknown', localImgPath=None):
        self.foldername = foldername
        self.filename = filename
        self.databaseSrc = databaseSrc
        self.imgSize = imgSize
        self.boxlist = []
        self.localImgPath = localImgPath
        self.verified = False

    def addBndBox(self, trackid, xmin, ymin, xmax, ymax, name, difficult):
        bndbox = {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}
        bndbox['trackid'] = trackid
        bndbox['name'] = name
        bndbox['difficult'] = difficult
        self.boxlist.append(bndbox)

    def BndBox2YoloLine(self, box, classList=[]):
        xmin = box['xmin']
        xmax = box['xmax']
        ymin = box['ymin']
        ymax = box['ymax']

        xcen = float((xmin + xmax)) / 2 / self.imgSize[1]
        ycen = float((ymin + ymax)) / 2 / self.imgSize[0]

        w = float((xmax - xmin)) / self.imgSize[1]
        h = float((ymax - ymin)) / self.imgSize[0]

        classIndex = classList.index(box['name'])

        trackid = box['trackid']

        return trackid, classIndex, xcen, ycen, w, h

    def BndBox2CustomLine(self, box, classList=[]):
        xmin = box['xmin']
        xmax = box['xmax']
        ymin = box['ymin']
        ymax = box['ymax']
        classIndex = classList.index(box['name'])

        trackid = box['trackid']

        return trackid, classIndex, xmin, ymin, xmax, ymax

    def save(self, classList=[], targetFile=None):

        out_file = None  # Update yolo .txt
        out_class_file = None  # Update class list .txt

        if targetFile is None:
            out_file = open(
                self.filename + TXT_EXT, 'w', encoding=ENCODE_METHOD)
            classesFile = os.path.join(os.path.dirname(os.path.abspath(self.filename)), "classes.txt")
            out_class_file = open(classesFile, 'w')

        else:
            out_file = codecs.open(targetFile, 'w', encoding=ENCODE_METHOD)
            classesFile = os.path.join(os.path.dirname(os.path.abspath(targetFile)), "classes.txt")
            out_class_file = open(classesFile, 'w')

        for box in self.boxlist:
            # trackid, classIndex, xcen, ycen, w, h = self.BndBox2YoloLine(box, classList)
            # print(trackid, classIndex, xcen, ycen, w, h)
            # out_file.write("%d, %d, %.6f, %.6f, %.6f, %.6f\n" % (trackid, classIndex, xcen, ycen, w, h))

            trackid, classIndex, xmin, ymin, xmax, ymax = self.BndBox2CustomLine(box, classList)
            print(trackid, xmin, ymin, xmax, ymax, classIndex)
            out_file.write("%d, %d, %d, %d, %d, %d\n" % (trackid, xmin, ymin, xmax, ymax, classIndex))

        print(classList)
        print(out_class_file)
        for c in classList:
            out_class_file.write(c + '\n')

        out_class_file.close()
        out_file.close()


class YoloReader:

    def __init__(self, filepath, image, classListPath=None):
        # shapes type:
        # [labbel, [(x1,y1), (x2,y2), (x3,y3), (x4,y4)], color, color, difficult]
        self.shapes = []
        self.filepath = filepath

        if classListPath is None:
            dir_path = os.path.dirname(os.path.realpath(self.filepath))
            self.classListPath = os.path.join(dir_path, "classes.txt")
        else:
            self.classListPath = classListPath

        print(filepath, self.classListPath)

        classesFile = open(self.classListPath, 'r')
        self.classes = classesFile.read().strip('\n').split('\n')

        print(self.classes)

        imgSize = [image.height(), image.width(),
                   1 if image.isGrayscale() else 3]

        self.imgSize = imgSize

        self.verified = False
        # try:
        self.parseYoloFormat()
        # except:
        # pass

    def getShapes(self):
        return self.shapes

    def addShape(self, trackid, label, xmin, ymin, xmax, ymax, difficult):

        points = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
        self.shapes.append((trackid, label, points, None, None, difficult))

    def yoloLine2Shape(self, classIndex, xcen, ycen, w, h):
        label = self.classes[int(classIndex)]

        xmin = max(float(xcen) - float(w) / 2, 0)
        xmax = min(float(xcen) + float(w) / 2, 1)
        ymin = max(float(ycen) - float(h) / 2, 0)
        ymax = min(float(ycen) + float(h) / 2, 1)

        xmin = int(self.imgSize[1] * xmin)
        xmax = int(self.imgSize[1] * xmax)
        ymin = int(self.imgSize[0] * ymin)
        ymax = int(self.imgSize[0] * ymax)

        return label, xmin, ymin, xmax, ymax

    def parseYoloFormat(self):
        bndBoxFile = open(self.filepath, 'r')
        for bndBox in bndBoxFile:
            # trackid, classIndex, xcen, ycen, w, h = bndBox.split(' ')
            # label, xmin, ymin, xmax, ymax = self.yoloLine2Shape(classIndex, xcen, ycen, w, h)/
            trackid, xmin, ymin, xmax, ymax, classIndex = bndBox.split(',')
            label = self.classes[int(classIndex)]

            # Caveat: difficult flag is discarded when saved as yolo format.
            self.addShape(int(trackid), label, int(xmin), int(ymin), int(xmax), int(ymax), False)
