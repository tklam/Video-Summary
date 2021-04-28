from PIL import Image
from pathlib import Path
import argparse
import imagehash
import itertools
import math
import os
import subprocess
import sys
import cv2

def crop_image(image_filename, x0, x1, y0, y1):
    img = cv2.imread(image_filename)

    # cut out the region containing the interesting region
    cropped_img = img[y0:y1, x0:x1]

    # By default OpenCV stores images in BGR format and since pytesseract assumes RGB format,
    # we need to convert from BGR to RGB format/mode:
    img_rgb = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2RGB)

    return img_rgb


def are_frames_similar(args, image_filename_1, image_filename_2):
    lower_hash_size = 16
    upper_hash_size = 8
    lower_diff_threshold = 35  # 10-35, use lower value for static screen # TODO 
    upper_diff_threshold = 30

    upper_1 = crop_image(image_filename_1, 0, 400, 0, 200)
    lower_1 = crop_image(image_filename_1, 0, 400, 200, 270) # the lower region probably contains the subtitles

    upper_2 = crop_image(image_filename_2, 0, 400, 0, 200)
    lower_2 = crop_image(image_filename_2, 0, 400, 200, 270)

    hash_upper_1 = imagehash.dhash(Image.fromarray(upper_1), hash_size=upper_hash_size)
    hash_lower_1 = imagehash.dhash(Image.fromarray(lower_1), hash_size=lower_hash_size)

    hash_upper_2 = imagehash.dhash(Image.fromarray(upper_2), hash_size=upper_hash_size)
    hash_lower_2 = imagehash.dhash(Image.fromarray(lower_2), hash_size=lower_hash_size)

    print(f'diff {image_filename_1} {image_filename_2} upper: {hash_upper_1-hash_upper_2} lower: {hash_lower_1-hash_lower_2}')

    lower_diff = hash_lower_1 - hash_lower_2 
    upper_diff = hash_upper_1 - hash_upper_2 
    if lower_diff < lower_diff_threshold:
        if upper_diff < upper_diff_threshold:
            # if the lower part is highly similar, and the uppwer part is quiie similar => similar
            return True
        else:
            # if the lower part is highly similar, but the uppwer part is not similar => not similar
            return False
    else:
        return False


def deduplication(args, file_pairs):
    removed_count = 0
    for name_1, name_2 in file_pairs:
        if not Path(name_1).is_file():
            continue
        if not Path(name_2).is_file():
            continue
        if are_frames_similar(args, name_1, name_2):
            os.rename(name_1, name_1+'.bak')
            removed_count = removed_count + 1
            print(f'    Rename {name_1} to {name_1}.bak')

    print(f'Removed {removed_count} frames because they are similar.')


def image_file_generator():
    img_paths = []
    for img_path in sorted(Path(r'./').glob('frame_*.jpg'), key=lambda path: float(path.stem.rsplit("_", 1)[1])):
        img_paths.append(img_path)

        if len(img_paths) == 2:
            yield (str(img_paths[0]), str(img_paths[1]))
            img_paths = [img_paths[1]]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Deduplicate consecutive images')
    args = parser.parse_args()

    file_pairs = image_file_generator()
    deduplication(args, file_pairs)
