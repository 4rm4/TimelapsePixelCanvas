#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import os
import math
import datetime
import sys
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout
from argparse import ArgumentParser

from PIL import Image
from retry_decorator import retry

from i18n import I18n



BLOCK_SIZE = 64
AREA_LEFT = 7
AREA_RIGHT = 8
TOTAL_AREA = AREA_LEFT + AREA_RIGHT
CHUNK_SIZE = TOTAL_AREA * BLOCK_SIZE

COLORS = [
    (255, 255, 255),
    (228, 228, 228),
    (136, 136, 136),
    (34, 34, 34),
    (255, 167, 209),
    (229, 0, 0),
    (229, 149, 0),
    (160, 106, 66),
    (229, 217, 0),
    (148, 224, 68),
    (2, 190, 1),
    (0, 211, 221),
    (0, 131, 199),
    (0, 0, 234),
    (207, 110, 228),
    (130, 0, 128)
]

URL = 'https://pixelcanvas.io/api/bigchunk/%s.%s.bmp'

@retry((HTTPError, ConnectionError, Timeout), tries=6, delay=3, backoff=2)
def download_bmp(x, y):
    resp = requests.get(URL % (x, y), headers={'User-agent':'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'}, stream=True)
    return bytearray(resp.content)

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-s' ,'--seconds', required=False, type=int, default=30, dest='seconds')
    parser.add_argument('-r', '--radius', required=False, type=int , default=1, dest='radius')
    parser.add_argument('-x', required=False, type=int, dest='x')
    parser.add_argument('-y', required=False, type=int, dest='y')
    parser.add_argument('-d','--directory', required=False, default='./', dest='directory')
    parser.add_argument('-sx', '--start_x', required=False, type=int, dest='start_x')
    parser.add_argument('-ex', '--end_x', required=False, type=int, dest='end_x')
    parser.add_argument('-sy', '--start_y', required=False, type=int, dest='start_y')
    parser.add_argument('-ey', '--end_y', required=False, type=int, dest='end_y')
    parser.add_argument('-v', '--verbose', required=False, default=False, dest='verbose', action='store_true')

    return parser.parse_args()

def valide_args(args):

    if all(v is None for v in [args.x, args.y]) and all(v is None for v in [args.start_x, args.end_x, args.start_y, args.end_y]):
        raise ValueError("It's necesary choose or the -x axis and -y axis or --start_y, --start_x, --end_y, --end_x arguments")

    if all(v is None for v in [args.x, args.y]) and None in [args.start_x, args.end_x, args.start_y, args.end_y]:
        raise ValueError("It's necessary fill all the parameters --start_y, --start_x, --end_y, --end_x")
    
    if None in [args.x, args.y] and all(v is None for v in [args.start_x, args.end_x, args.start_y, args.end_y]):
        raise ValueError("It's necessary fill all the parameters -x, -y")

    if all(not v is None for v in [args.x, args.y]) and all(not v is None for v in [args.start_x, args.end_x, args.start_y, args.end_y]):
        raise ValueError('You need pick or the -x axis and -y axis or --start_y, --start_x, --end_y, --end_x arguments')

    if args.seconds < 1:
        raise ValueError("The seconds must be positive and non-zero")

    if all(not v is None for v in [args.x, args.y]):
        if args.radius < 1:
            raise ValueError("The radius must be positive and non-zero and odd")

        if not args.radius % 2:
            raise ValueError("The radius must be odd")  


def calc_max_chunks(arg_chunks, start_x, end_x, start_y, end_y):
    # if using bounded area arguments
    if all(not v is None for v in [start_x, end_x, start_y, end_y]):
        width = end_x - start_x
        height = end_y - start_y

        chunks_x = abs(width / CHUNK_SIZE)
        chunks_y = abs(height / CHUNK_SIZE)
        max_chunks = int(math.ceil(chunks_x if chunks_x >= chunks_y else chunks_y))
        return (max_chunks if max_chunks % 2 else max_chunks + 1)
    return arg_chunks

def calc_size_area(chunks):
    return chunks * CHUNK_SIZE

def get_midpoint(x, y, start_x, end_x, start_y, end_y):
    if all(not v is None for v in [x, y]):
        return x, y

    width = end_x - start_x
    height = end_y - start_y

    return (2 * start_x + width) // 2, (2 * start_y + height) // 2

def setup_map_image(num_blocks, middle_x, middle_y):
    map_image = {}
    last = 0
    for x in range((middle_x - (num_blocks + AREA_LEFT)) * BLOCK_SIZE, (num_blocks + AREA_RIGHT + middle_x) * BLOCK_SIZE):
        map_image[x] = {}
        for y in range((middle_y - (num_blocks + AREA_LEFT)) * BLOCK_SIZE, (num_blocks + AREA_RIGHT + middle_y) * BLOCK_SIZE):
            map_image[x][y] = None
    return map_image

def get_num_blocks(max_chunks):
    return int(math.ceil(max_chunks / 2) * TOTAL_AREA)


def calc_centers_axis(middle_x, middle_y):
    center_x = (middle_x - (middle_x % 64)) // 64
    center_y = (middle_y - (middle_y % 64)) // 64
    offset_x = center_x % 15
    offset_y = center_y % 15
    return center_x - offset_x, center_y - offset_y, offset_x, offset_y

def bigchunk(max_chunks, middle_x, middle_y, verbose):
    center_block_x, center_block_y, offset_x, offset_y = calc_centers_axis(middle_x, middle_y)

    num_blocks = get_num_blocks(max_chunks)


    if offset_x is not 0:
        end = (center_block_x + offset_x + num_blocks) * 64
        if verbose:
            print(I18n.get('blind east of %s') % end)
    if offset_y is not 0:
        end = (center_block_y + offset_y + num_blocks) * 64
        if verbose:
            print(I18n.get('blind south of %s') % end)

    # matrix
    map_image = setup_map_image(num_blocks, center_block_x, center_block_y)

    cx_range = range(center_block_x - num_blocks, 1 + center_block_x + num_blocks, TOTAL_AREA)
    cy_range = range(center_block_y - num_blocks, 1 + center_block_y + num_blocks, TOTAL_AREA)

    total_chunks = len(cx_range) * len(cy_range)
    chunk_count = 0

    for center_x in cx_range:
        for center_y in cy_range:
            if verbose:
                print(I18n.get('Loading chunk (%s, %s)...') % (center_x, center_y))
            else:
                chunk_count += 1
                print(I18n.get('>> Loading canvas [%s/%s]', True) % (chunk_count, total_chunks), end='\r', flush=True)
            raw = download_bmp(center_x, center_y)
            index = 0
            for block_y in range(center_y - AREA_LEFT, center_y + AREA_RIGHT):
                for block_x in range(center_x - AREA_LEFT, center_x + AREA_RIGHT):
                    for y in range(BLOCK_SIZE):
                        actual_y = (block_y * BLOCK_SIZE) + y
                        for x in range(0, BLOCK_SIZE, 2):
                            actual_x = (block_x * BLOCK_SIZE) + x
                            map_image[actual_x    ][actual_y] = raw[index] >> 4
                            map_image[actual_x + 1][actual_y] = raw[index] & 0x0F
                            index += 1
    if not verbose:
        print('', end='\r')
    return map_image

def get_sizes(chunks, x, y, start_x, end_x, start_y, end_y):
    if all(not v is None for v in [start_x, end_x, start_y, end_y]):
        return abs(end_x - start_x), abs(end_y - start_y)
    return abs(calc_size_area(chunks)), abs(calc_size_area(chunks))

def create_image(width, height):
    image = Image.new('RGB', (width, height), (255,255,255))
    pix = image.load()
    return image, pix

def convert_custom_image(map_image, pix, start_x, end_x, start_y, end_y):   
    minor_x = (start_x if start_x < end_x else end_x)
    bigger_x = (start_x if start_x > end_x else end_x)

    minor_y = (start_y if start_y < end_y else end_y)
    bigger_y = (start_y if start_y > end_y else end_y)
    pix_x, pix_y = 0, 0
    
    for x in range(minor_x, bigger_x ):
        pix_y = 0
        for y in range(minor_y, bigger_y):
            pix[pix_x, pix_y] = COLORS[map_image[x][y]]
            pix_y += 1
        pix_x += 1

    return pix

def convert_image_total(map_image, pix, chunks, middle_x, middle_y):
    num_blocks = get_num_blocks(chunks)
    pix_x, pix_y = 0, 0

    for y in range((middle_y - (num_blocks + AREA_LEFT)) * BLOCK_SIZE, (middle_y + (num_blocks + AREA_RIGHT)) * BLOCK_SIZE):
        pix_x = 0
        for x in range((middle_x - (num_blocks + AREA_LEFT))* BLOCK_SIZE, (middle_y + (num_blocks + AREA_RIGHT)) * BLOCK_SIZE):
            pix[pix_x, pix_y] = COLORS[map_image[x][y]]
            pix_x += 1
        pix_y += 1
    return pix

def save_image(image, directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    name_file = os.path.join(directory, datetime.datetime.utcnow().strftime("%Y%m%d%H%M%SUTC") + '.png')
    image.save(name_file)
    print(I18n.get('Saved %s') % name_file)

def download_save_image(directory, chunks, width, height, middle_x, middle_y, start_x, start_y, end_x, end_y, verbose):
    map_image = bigchunk(chunks, middle_x, middle_y, verbose)

    image, pix = create_image(width, height)

    if all(not v is None for v in [start_x, end_x, start_y, end_y]):
        image.pix = convert_custom_image(map_image, pix, start_x, end_x, start_y, end_y)
    else:
        image.pix = convert_image_total(map_image, pix, chunks, middle_x, middle_y)
    
    save_image(image, directory)

def main():
    args = parse_args()

    valide_args(args)

    middle_x, middle_y = get_midpoint(args.x, args.y, args.start_x, args.end_x, args.start_y, args.end_y)

    max_chunks = calc_max_chunks(args.radius, args.start_x, args.end_x, args.start_y, args.end_y)

    width, height = get_sizes(max_chunks, args.x, args.y, args.start_x, args.end_x, args.start_y, args.end_y)   
    
    if max_chunks > 5 and raw_input(I18n.get('rad > 5 prompt')) in ['y']:
        raise KeyboardInterrupt()
    

    while True:
        download_save_image(args.directory, max_chunks, width, height, middle_x, middle_y, args.start_x, args.start_y, args.end_x, args.end_y, args.verbose)
        print(I18n.get('Waiting %s seconds') % args.seconds)
        time.sleep(args.seconds)
        

if __name__ == '__main__':  
    try:
        main()
    except KeyboardInterrupt:
        print()
        print(I18n.get('Quitting'))