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
import pytesseract
import difflib
import threading

subtitles_simil_threshold = 0.5

frames_subtitles = {}

def show_img(debug, caption, cv_image):
    if not debug:
        return
    cv2.imshow(caption, cv_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def crop_and_black_and_white(image_filename, x0, x1, y0, y1, is_white_subtitle, binary_threshold, debug):
    img = cv2.imread(image_filename)
    if debug:
        print(f'Image dimension: {img.shape}')
    show_img(debug, 'Original', img)

    # cut out the region containing the subtitle  
    cropped_img = img[y0:y1, x0:x1]
    show_img(debug, 'Cropped', cropped_img)

    # grayscale
    gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
    show_img(debug, 'Grayscaled', gray)

    # black and white
    ret, bw = cv2.threshold(gray, binary_threshold, 255, cv2.THRESH_BINARY)
    # bw = cv2.adaptiveThreshold(gray, 255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,9,2)
    show_img(debug, 'Black and white', bw)

    # make the text black
    if is_white_subtitle:
        bw = cv2.bitwise_not(bw)
        show_img(debug, 'Inverted black and white', bw)

    # By default OpenCV stores images in BGR format and since pytesseract assumes RGB format,
    # we need to convert from BGR to RGB format/mode:
    img_rgb = cv2.cvtColor(bw, cv2.COLOR_BGR2RGB)
    show_img(debug, 'RGB img', img_rgb)

    return img_rgb


def ocr_subtitle(image_filename, x0, x1, y0, y1, is_white_subtitle, debug, binary_thresholds):
    custom_oem_psm_configs = [r'--oem 3 --psm 3', r'--oem 3 --psm 6', r'--oem 3 --psm 11']

    success_thresholds = [] # (threshold, subtitle)

    def try_crop(b):
        return crop_and_black_and_white(image_filename, 
                x0, x1, y0, y1,
                is_white_subtitle,
                b,
                debug)

    def is_recognised_valid(subtitle):
        stripped_subtitle = None
        if subtitle is not None:
            stripped_subtitle = subtitle.strip()
        else:
            stripped_subtitle = ''

        if stripped_subtitle == '':
            return False
        if '\n' in stripped_subtitle  or '\r' in stripped_subtitle: # assume there is only one line #TODO
            return False
        if len(stripped_subtitle) < 2: # assume the sentence length >=2 #TODO
            return False
        return True

    def thread_work(c, success_thresholds):
        for b in binary_thresholds:
            bw_maybe_subtitle = try_crop(b)
            subtitle = pytesseract.image_to_string(bw_maybe_subtitle, lang='chi_tra', config=c)
            if is_recognised_valid(subtitle):
                if debug:
                    print(f'Finding binary threshold from large to small: {b}: {subtitle}')
                success_thresholds.append((b, subtitle))

    # TODO change to multiprocessing
    thread_list = []
    for c in custom_oem_psm_configs:
        thread = threading.Thread(target=thread_work, args=(c, success_thresholds))
        thread_list.append(thread)
    for thread in thread_list:
         thread.start()
    for thread in thread_list:
         thread.join()

#    for c in custom_oem_psm_configs:
#        for b in binary_thresholds:
#            bw_maybe_subtitle = try_crop(b)
#            subtitle = pytesseract.image_to_string(bw_maybe_subtitle, lang='chi_tra', config=c)
#            if is_recognised_valid(subtitle.replace(' ','')):
#                if debug:
#                    print(f'Finding binary threshold from large to small: {b}: {subtitle}')
#                success_thresholds.append((b, subtitle))

    if len(success_thresholds) == 0:
        return None

    # prefer much higher binary_threshold
    success_thresholds.sort(key=lambda x:x[0], reverse=True)

    if len(success_thresholds) > 1:
        guess_binary_threshold, guess_subtitle = success_thresholds[-2] # the last but one largest

        largest_similarity = 0

        for i in range(0, len(success_thresholds)-1):
            b, subtitle = success_thresholds[i]
            next_b, next_subtitle = success_thresholds[i+1]
            similarity = difflib.SequenceMatcher(lambda x: x==' ', subtitle, next_subtitle).ratio() 
            if similarity > largest_similarity and len(subtitle) > len(guess_subtitle):
                largest_similarity = similarity
                guess_binary_threshold = b
                guess_subtitle = subtitle
    else:
        guess_binary_threshold, guess_subtitle = success_thresholds[0]

    if debug:
        print(f'Guess binary threshold: {guess_binary_threshold}')

    return guess_subtitle.strip()


def crop_image(image_filename, x0, x1, y0, y1):
    img = cv2.imread(image_filename)

    # cut out the region containing the interesting region
    cropped_img = img[y0:y1, x0:x1]

    # By default OpenCV stores images in BGR format and since pytesseract assumes RGB format,
    # we need to convert from BGR to RGB format/mode:
    img_rgb = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2RGB)

    return img_rgb


def are_frames_similar(args, image_filename_1, image_filename_2):
    # Divide a frame into the upper and lower part. The lower region probably contains the subtitles.

    upper_lower_ratio = 2.857142857142857 # pixels of the upper part/pixels of the lower part: ~ 3:1
    lower_hash_size = 16
    upper_hash_size = 8

    # TODO make these automatically determined, or abstract them and let the user choose an option instead of settings values
    lower_diff_threshold = args.lower_similarity_threshold # 10-35, use lower value for static screen 
    upper_diff_threshold = args.upper_similarity_threshold

    lower_part_size = math.ceil(args.height_pixel / (1+upper_lower_ratio))
    upper_part_size = args.height_pixel - lower_part_size

    upper_1 = crop_image(image_filename_1, 0, args.width_pixel, 0, upper_part_size)
    lower_1 = crop_image(image_filename_1, 0, args.width_pixel, upper_part_size, args.height_pixel)

    upper_2 = crop_image(image_filename_2, 0, args.width_pixel, 0, upper_part_size)
    lower_2 = crop_image(image_filename_2, 0, args.width_pixel, upper_part_size, args.height_pixel)

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
        if not args.use_subtitles:
            return False

        # comparing the subtitles detected

        # assume upper_lower_ratio > 1,
        # upper_lower_ratio = y1 / (y1 - y0)
        # -> y0 = (upper_lower_ratio * y1 - y1) / upper_lower_ratio
        x1,y1 = (args.width_pixel, args.height_pixel)
        x0,y0 = (int(0), int(y1*(upper_lower_ratio -1)/upper_lower_ratio)) 
        is_white_subtitle = True

        subtitle_1 = frames_subtitles[image_filename_1] if image_filename_1 in frames_subtitles else ocr_subtitle(image_filename_1, x0, x1, y0, y1, is_white_subtitle, False, args.binary_thresholds)
        subtitle_2 = frames_subtitles[image_filename_2] if image_filename_2 in frames_subtitles else ocr_subtitle(image_filename_2, x0, x1, y0, y1, is_white_subtitle, False, args.binary_thresholds)

        print(f'      detected subtitles of {image_filename_1}: {subtitle_1}')
        print(f'      detected subtitles of {image_filename_2}: {subtitle_2}')

        frames_subtitles[image_filename_1] = subtitle_1
        frames_subtitles[image_filename_2] = subtitle_2

        if subtitle_1 is not None and subtitle_2 is not None:
            seqMatch = difflib.SequenceMatcher(a=subtitle_1.replace(' ',''), b=subtitle_2.replace(' ',''))
            print(f'        similarity: {seqMatch.ratio()}')
            if seqMatch.ratio() > subtitles_simil_threshold:
                return True
        else:
            return False


def deduplication(args, file_pairs):
    removed_count = 0
    for name_1, name_2 in file_pairs:
        if not Path(name_1).is_file():
            continue
        if not Path(name_2).is_file(): continue
        if are_frames_similar(args, name_1, name_2):
            os.rename(name_1, name_1+'.bak')
            removed_count = removed_count + 1
            print(f'    Rename {name_1} to {name_1}.bak')

    print(f'Removed {removed_count} frames because they are similar.')


def image_file_generator():
    img_paths = []
    # rename previously 'removed' images
    for img_path in Path(r'./').glob('frame_*.jpg.bak'):
        name = str(img_path)
        os.rename(name, name.replace('.jpg.bak', '.jpg'))

    # collect and sort the frames captured
    for img_path in sorted(Path(r'./').glob('frame_*.jpg'), key=lambda path: float(path.stem.rsplit("_", 1)[1])):
        img_paths.append(img_path)

        if len(img_paths) == 2:
            yield (str(img_paths[0]), str(img_paths[1]))
            img_paths = [img_paths[1]]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Deduplicate consecutive images')
    parser.add_argument('--width_pixel', required=True, default=480, type=int,
            help='Set the width of the video in pixels')
    parser.add_argument('--height_pixel', required=True, default=270, type=int,
            help='Set the height of the video in pixels')
    parser.add_argument('--upper_similarity_threshold', required=False, default=30, type=float,
            help='The upper part of two consecutive images are regarded as similar if their hash \
            values are below this threshold. The smaller the value, the harder for two frames to be \
            similar')
    parser.add_argument('--lower_similarity_threshold', required=False, default=30, type=float,
            help='The lower part of two consecutive images are regarded as similar if their hash \
            values are below this threshold. The smaller the value, the harder for two frames to be \
            similar')
    parser.add_argument('--use_subtitles', required=False, action="store_true", default=False, help="Fast or take subtitles into account if specified")
    args = parser.parse_args()

    if not args.use_subtitles:
        print('Using fast deduplication method')
    else:
        print('Using probably more accurate deduplication method: comparing the subtitles detected')

    #args.binary_thresholds = [i for i in range(255, 128, -5)]
    args.binary_thresholds = [i for i in range(250, 150, -20)] 

    file_pairs = image_file_generator()
    deduplication(args, file_pairs)
