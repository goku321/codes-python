#!/usr/bin/python

import os, sys
from PIL import Image

def shrink_size(path, width, max_size):
    if __name__ != '__main__':
        if not path:
            print('Error: path cannot be empty')
            return

        try:
            int(width)

        except ValueError:
            print('Error: width must be an integer')
            return

        else:
            width = int(width)

        try:
            int(max_size)

        except ValueError:
            print('Error: max_size must be an integer')
            return

        else:
            max_size = int(max_size)

    try:
        img = Image.open(path)
    
    except FileNotFoundError:
        print('file ' + path + ' does not exist.')

    except OSError:
        print(path + ' is not an image file.')

    else:
        (img_width, img_height) = img.size

        if img_width > width:
            wpercent = (width/float(img_width))
            height = int((float(img_height)*float(wpercent)))
            img = img.resize((width, height), Image.ANTIALIAS)
            img.save(path)

        size_in_kb = os.path.getsize(path) >> 10
        print(size_in_kb)

        quality = 100

        while size_in_kb > max_size:
            quality -= 5
            img.save(path, optimize=True, quality=quality)
            size_in_kb = os.path.getsize(path) >> 10
            print(size_in_kb)

        img.save(path)

#main
if __name__ == '__main__':
    if len(sys.argv) == 4:
        path = sys.argv[1]
        try:
            os.chdir(sys.argv[1])

        except FileNotFoundError:
            print('Error: directory ' + path + ' does not exist.')
            os._exit(2)

        try:
            int(sys.argv[2])
            int(sys.argv[3])

        except ValueError:
            print('Error: width/max_size must be an integer')
            sys.exit()

        else:
            width = int(sys.argv[2])
            max_size = int(sys.argv[3])

        for filename in os.listdir():
            shrink_size(filename, width, max_size)

    else:
        print('usage: shrink_image_size [path] [width] [max_size]')
