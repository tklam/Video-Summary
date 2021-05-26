from PIL import Image
from pathlib import Path
import argparse
import imagehash
import itertools
import math
import os
import subprocess
import sys
import multiprocessing as mp


def get_video_duration(input_video):
    cmd = ["ffprobe", "-i", input_video, "-show_entries", "format=duration",
           "-v", "quiet", "-of", "csv=p=0"]
    duration_seconds = subprocess.check_output(cmd).decode("utf-8").strip()

    if duration_seconds == 'N/A':
        cmd = ["soxi", "-D", "32k-audio.wav"]
        duration_seconds = subprocess.check_output(cmd).decode("utf-8").strip()

    return float(duration_seconds)


def extract_frame(time_in_seconds, input_video, output_image):
    if Path(output_image).is_file():
        return output_image

    p = subprocess.run(['ffmpeg'] + 
            f'-ss {time_in_seconds} -y -i {input_video} -vframes 1 -q:v 2 {output_image}'.split(),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if p.returncode != 0:
        print(f'An error occurred at {time_in_seconds}')
        return None

    return output_image


def extract_speech_time(speech_time_log):
    with open(speech_time_log, 'r') as log:
        for l in log.readlines():
            tokens = l.split()
            if len(tokens) < 2:
                continue
            start_time = round(float(tokens[0]),1)
            end_time = round(float(tokens[1]),1)
            mid_time = round((end_time + start_time) / 2.0, 1)
            timestamps = [start_time, mid_time, end_time]
            yield timestamps


def gen_regular_timestamps(duration_secs, interval):
    t = 0.0
    yield t

    while t < duration_secs:
        t = t + interval
        yield t


def do_extract_frame(t, frames_filenames, args):
    rounded_time = round(t,1)
    filename = f'frame_{rounded_time}.jpg'
    if len(frames_filenames) > 0 and filename == frames_filenames[-1]:
        return
    filename = extract_frame(t, args.input_video, filename)
    if filename is not None:
        frames_filenames.append(filename)


def extract_main(args):
    interesting_timestamps = []
    speech_timestampes_indexes = set({})

    # load the timestamps of speech
    speech_timestamps = iter(extract_speech_time(args.speech_time_log))

    for r in gen_regular_timestamps(args.duration_secs, args.time_interval):
        has_some_non_regular = False
        prev_len = len(interesting_timestamps)

        # speech
        while True:
            try:
                ts = next(speech_timestamps) # TODO mid_time and end_time is not being used
            except StopIteration:
                break

            do_break = False 
            i=0
            for t in ts:
                if t < r:
                    interesting_timestamps.append(t)
                    speech_timestampes_indexes.add(len(interesting_timestamps)-1)
                    i=i+1
                elif t > r:
                    speech_timestamps = itertools.chain([ts[i:]], speech_timestamps)
                    do_break = True
                    break
                else:
                    do_break = True
                    break

            if do_break:
                break

        if len(interesting_timestamps) > prev_len:
            has_some_non_regular = True

        if not has_some_non_regular:
            interesting_timestamps.append(r)

    frames_filenames = []
    # extract the frames
    with mp.Pool(8) as p:
        p.starmap(do_extract_frame, [[t, frames_filenames, args] for t in interesting_timestamps])

    return frames_filenames, speech_timestampes_indexes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract frames from a video at some particular timestamps')
    parser.add_argument('--input_video', required=True, default=None,
            help='Set the time of the frame to be extracted.')
    parser.add_argument('--speech_time_log', required=True, default=None,
            help='A log file containing lines of speech segment information in the following format: \
            <start time> <end time> <wav filename>.')
    parser.add_argument('--time_interval', required=False, default=1, type=float,
            help='Define the time interval that a frame should be captured regularly (in seconds).')
    parser.add_argument('--only_get_video_duration', required=False, action="store_true",
            default=None, help='Report the video duration in seconds and quit.')

    args = parser.parse_args()

    duration_secs = get_video_duration(args.input_video)
    args.duration_secs = duration_secs
    print(f'Video: {args.input_video} length in seconds: {duration_secs}')

    if args.only_get_video_duration:
        sys.exit(0)

    extracted_frames_filenames, speech_timestampes_indexes = extract_main(args)
