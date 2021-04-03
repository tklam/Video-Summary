import argparse
import os
import subprocess


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract one frame from a video at a particular time')
    parser.add_argument('--input_video', required=True, default=None, help='Set the time of the frame to be extracted')
    parser.add_argument('--speech_time_log', required=True, default=None,
            help='A log file containing lines of speech segment information in the following format: <start time> <end time> <wav filename>')

    args = parser.parse_args()

    frame_counter = 0
    for start_time, mid_time, end_time in extract_speech_time(args.speech_time_log):
        extract_frame(start_time, args.input_video, f'frame_{frame_counter}.jpg')
        frame_counter += 1
        #extract_frame(mid_time, args.input_video, f'frame_{frame_counter}.jpg')
        #frame_counter += 1
        #extract_frame(end_time, args.input_video, f'frame_{frame_counter}.jpg')
        #frame_counter += 1

