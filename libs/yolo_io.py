#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
import os
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from lxml import etree
import codecs
from libs.constants import DEFAULT_ENCODING
from libs.utils import calc_distance, calc_extra_points, calc_shib
from PyQt5.QtCore import QPointF

CSV_EXT = '.csv'
ENCODE_METHOD = DEFAULT_ENCODING


class YOLOWriter:

    def __init__(self, folder_name, filename, img_size, database_src='Unknown', local_img_path=None):
        self.folder_name = folder_name
        self.filename = filename
        self.database_src = database_src
        self.img_size = img_size
        self.box_list = []
        self.local_img_path = local_img_path
        self.verified = False

    def add_bnd_box(self, points, name, difficult):
        bnd_box = {}
        bnd_box['points'] = points
        bnd_box['name'] = name
        bnd_box['difficult'] = difficult
        self.box_list.append(bnd_box)

    def bnd_box_to_yolo_line(self, box, class_list=[]):
        # PR387
        box_name = box['name']
        if box_name not in class_list:
            class_list.append(box_name)
        return box['points'][0][0], box['points'][0][1], box['points'][1][0], box['points'][1][1], box_name

    def save(self, class_list=[], target_file=None):

        out_file = None  # Update yolo .txt
        out_class_file = None   # Update class list .txt

        if target_file is None:
            out_file = open(
                self.filename + CSV_EXT, 'w', encoding=ENCODE_METHOD)
            classes_file = os.path.join(os.path.dirname(
                os.path.abspath(self.filename)), "classes.txt")
            out_class_file = open(classes_file, 'w')

        else:
            out_file = codecs.open(target_file, 'w', encoding=ENCODE_METHOD)
            classes_file = os.path.join(os.path.dirname(
                os.path.abspath(target_file)), "classes.txt")
            out_class_file = open(classes_file, 'w')

        for box in self.box_list:
            x_center, y_center, x_edge, y_edge, class_name = self.bnd_box_to_yolo_line(
                box, class_list)
            # print (classIndex, x_center, y_center, w, h)
            out_file.write("%.6f,%.6f,%.6f,%.6f,%s\n" %
                           (x_center, y_center, x_edge, y_edge, class_name))

        # print (classList)
        # print (out_class_file)
        for c in class_list:
            out_class_file.write(c+'\n')

        out_class_file.close()
        out_file.close()


class YoloReader:

    def __init__(self, file_path, image, class_list_path=None):
        # shapes type:
        # [labbel, [(x1,y1), (x2,y2), (x3,y3), (x4,y4)], color, color, difficult]
        self.shapes = []
        self.file_path = file_path

        if class_list_path is None:
            dir_path = os.path.dirname(os.path.realpath(self.file_path))
            self.class_list_path = os.path.join(dir_path, "classes.txt")
        else:
            self.class_list_path = class_list_path

        # print (file_path, self.class_list_path)

        classes_file = open(self.class_list_path, 'r')
        self.classes = classes_file.read().strip('\n').split('\n')

        # print (self.classes)

        img_size = [image.height(), image.width(),
                    1 if image.isGrayscale() else 3]

        self.img_size = img_size

        self.verified = False
        # try:
        self.parse_yolo_format()
        # except:
        #     pass

    def get_shapes(self):
        return self.shapes

    def add_shape(self, x_center, y_center, x_edge, y_edge, label, difficult):
        init_pos, target_pos = QPointF(
            x_center, y_center), QPointF(x_edge, y_edge)
        p1, p2 = calc_extra_points(-1/(calc_shib(init_pos, target_pos)),
                                   init_pos, max_d=calc_distance(init_pos, target_pos) / 2)

        points = [(x_center, y_center), (p1.x(), p1.y()),
                  (x_edge, y_edge), (p2.x(), p2.y())]
        self.shapes.append((label, points, None, None, difficult))

    def parse_yolo_format(self):
        bnd_box_file = open(self.file_path, 'r')
        for bndBox in bnd_box_file:
            x_center, y_center, x_edge, y_edge, class_name = bndBox.strip().split(',')

            # Caveat: difficult flag is discarded when saved as yolo format.
            self.add_shape(float(x_center), float(y_center), float(x_edge),
                           float(y_edge), class_name, False)
