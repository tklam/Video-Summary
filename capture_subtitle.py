from pathlib import Path
from PIL import Image
import argparse
import cv2
import difflib
import math
import os
import pytesseract


# If you don't have tesseract executable in your PATH, include the following:
## pytesseract.pytesseract.tesseract_cmd = r'<full_path_to_your_tesseract_executable>'
## Example tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract'

# Simple image to string
## print(pytesseract.image_to_string(Image.open('test.png')))


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


def ocr_subtitle(args, binary_thresholds):
    # custom_oem_psm_config = r'--oem 3 --psm 6'

    success_thresholds = [] # (threshold, subtitle)

    def try_crop(b):
        return crop_and_black_and_white(args.input_image,
                args.x0, args.x1, args.y0, args.y1,
                args.is_white_subtitle,
                b,
                args.debug)

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

    for b in binary_thresholds:
        bw_maybe_subtitle = try_crop(b)
        subtitle = pytesseract.image_to_string(bw_maybe_subtitle, lang='chi_tra')
        if is_recognised_valid(subtitle):
            if args.debug:
                print(f'Finding binary threshold from large to small: {b}: {subtitle}')
            success_thresholds.append((b, subtitle))

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

    if args.debug:
        print(f'Guess binary threshold: {guess_binary_threshold}')

    return guess_subtitle.strip()


def gen_binary_search_binary_thresholds(smallest, largest, binary_thresholds, is_prefer_upper):
    if smallest >= largest:
        return

    if is_prefer_upper:
        average = math.ceil((largest + smallest)/2)
        gen_binary_search_binary_thresholds(average, largest, binary_thresholds, is_prefer_upper);
        binary_thresholds.append(average)
    else:
        average = math.floor((largest - smallest)/2)
        gen_binary_search_binary_thresholds(smallest, average, binary_thresholds, is_prefer_upper);
        binary_thresholds.append(average)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='La la la')
    parser.add_argument('--input_image', required=False, default=None,
            help='Path to the input image')
    parser.add_argument('--x0', required=True, default=None, type=int,
            help='Top left x')
    parser.add_argument('--x1', required=True, default=None, type=int,
            help='Bottom right x')
    parser.add_argument('--y0', required=True, default=None, type=int,
            help='Top left y')
    parser.add_argument('--y1', required=True, default=None, type=int,
            help='Bottom right y')
    parser.add_argument('--is_white_subtitle', required=False, default=False, action='store_true',
            help='Whether the subtitle is white')
    parser.add_argument('--binary_threshold', required=False, default=-1, type=int,
            help='Threshold for turning the image black and white')
    parser.add_argument('--debug', required=False, default=False, action='store_true')

    args = parser.parse_args()

    if args.debug:
        print('Supported OCR langs:')
        print(pytesseract.get_languages(config=''))

    binary_thresholds = []
    if args.binary_threshold == -1:
        gen_binary_search_binary_thresholds(0, 255, binary_thresholds, True)
        gen_binary_search_binary_thresholds(0, 255, binary_thresholds, False)
        #binary_thresholds = [i for i in range(255, -1, -5)]
    else:
        binary_thresholds = [args.binary_threshold]

    if args.input_image is not None:
        subtitle = ocr_subtitle(args, binary_thresholds)
        if subtitle is not None:
            print(subtitle)
    else:
        for img_path in sorted(Path(r'./').glob('frame_*.jpg'), key=lambda path: float(path.stem.rsplit("_", 1)[1])):
            args.input_image = str(img_path)
            subtitle = ocr_subtitle(args, binary_thresholds)
            if subtitle is not None:
                print(subtitle)
