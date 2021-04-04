import argparse
import itertools
import math
import os
import subprocess
import sys


def get_video_duration(input_video):
    cmd = ["ffprobe", "-i", input_video, "-show_entries", "format=duration",
           "-v", "quiet", "-of", "csv=p=0"]
    return float(subprocess.check_output(cmd).decode("utf-8").strip())


def extract_frame(time_in_seconds, input_video, output_image):
    p = subprocess.run(['ffmpeg'] + 
            f'-ss {time_in_seconds} -y -i {input_video} -vframes 1 -q:v 2 {output_image}'.split())
    if p.returncode != 0:
        print(f'An error occurred at {time_in_seconds}')


def extract_speech_time(speech_time_log):
    with open(speech_time_log, 'r') as log:
        for l in log.readlines():
            tokens = l.split()
            if len(tokens) < 2:
                continue
            start_time = float(tokens[0])
            end_time = float(tokens[1])
            mid_time = (end_time - start_time) / 2.0
            yield (start_time, mid_time, end_time)


def extract_main(args):
    interesting_timestamps = []
    regular_timestamps = [t for t in range(0, math.ceil(duration_secs)+args.time_interval, args.time_interval)]

    # load the timestamps of speech
    speech_timestamps = iter(extract_speech_time(args.speech_time_log))

    for r in regular_timestamps:
        has_some_non_regular = False
        prev_len = len(interesting_timestamps)

        # speech
        while True:
            try:
                s_start_time, s_mid_time, s_end_time = next(speech_timestamps) # TODO mid_time and end_time is not being used
            except StopIteration:
                break

            if s_start_time < r:
                interesting_timestamps.append(s_start_time)
            elif s_start_time > r:
                speech_timestamps = itertools.chain([(s_start_time, s_mid_time, s_end_time)], speech_timestamps)
                break
            else:
                break

        if len(interesting_timestamps) > prev_len:
            has_some_non_regular = True

        if not has_some_non_regular:
            interesting_timestamps.append(r)

    # extract the frames
    for t in interesting_timestamps:
        rounded_time = round(t)
        extract_frame(t, args.input_video, f'frame_{rounded_time}.jpg')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract frames from a video at some particular timestamps')
    parser.add_argument('--input_video', required=True, default=None,
            help='Set the time of the frame to be extracted.')
    parser.add_argument('--speech_time_log', required=True, default=None,
            help='A log file containing lines of speech segment information in the following format: \
            <start time> <end time> <wav filename>.')
    parser.add_argument('--time_interval', required=False, default=5, type=int,
            help='Define the time interval that a frame should be captured regularly (in seconds).')
    parser.add_argument('--only_get_video_duration', required=False, action="store_true",
            default=None, help='Report the video duration in seconds and quit.')

    args = parser.parse_args()

    duration_secs = get_video_duration(args.input_video)
    print(f'Video: {args.input_video} length in seconds: {duration_secs}')

    if args.only_get_video_duration:
        sys.exit(0)

    extract_main(args)
