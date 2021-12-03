from contextlib import redirect_stdout
from enum import Enum
import argparse
import collections
import contextlib
import deduplication
import importlib  
import math
import os
import pathlib
import subprocess as sp
import sys
extract_video_frames = importlib.import_module('extract-video-frames')
find_speech = importlib.import_module('find-speech')
gen_pptx = importlib.import_module('gen-pptx')


extract_frames_time_interval = 1.0 # capture 1 frame per second
video_id=''
video_url=None
video_file_path=None
upper_similarity_threshold=1.0
lower_similarity_threshold=1.0
need_change_dir=False
use_subtitles_to_deduplicate=False
pptx_pixels_per_cm = 56.69291338582677
remote_video_subtitle_lang=None
run_stages=[]

crop_width_pixel=0
crop_height_pixel=0
crop_x_offset=0
crop_y_offset=0

width_pixel=0
height_pixel=0

scaled_height_pixel=270 # suppose we want the final frame to have height: 270 pixels (~ 4.7 cm when printed) #TODO
scaled_width_pixel=0

find_speech_log='./find-speech.log'


class RunStage(Enum):
    Download = "download"
    LocateSpeechSegments = "segment_speech"
    CollectFrames = "collect_frames"
    DownSampleFrames = "down_sample_frames"
    DeduplicateFrames = "deduplicate_frames"
    GeneratePptx = "generate_pptx"


class DummyArgs(object):
    pass

def run_binary(binary_name, arguments):
    result = sp.run([binary_name] + arguments.split())


def run_binary_and_get_stdout(binary_name, arguments):
    result = sp.run([binary_name] + arguments.split(), stdout=sp.PIPE, stderr=None)
    return result.stdout.decode('utf-8')


def check_remote_video_subtitles():
    print('//------------------------------ List of subtitles available')
    result = run_binary_and_get_stdout('youtube-dl', f'--list-subs --skip-download {video_url}')
    print(result)


def download_remote_video_and_set_local_path():
    global video_file_path

    print('//------------------------------ Download the video')
    if remote_video_subtitle_lang is None:
        run_binary('youtube-dl',  f'-v {video_url} -o video')
        result = run_binary_and_get_stdout('ls',  f'-altr video.*')
    else:
        run_binary('youtube-dl', f'-v --embed-subs --write-sub --convert-subtitles srt --sub-lang {remote_video_subtitle_lang} {video_url} -o video')
        result = run_binary_and_get_stdout('ls',  f'-altr {os.getcwd()}/video.*')

    # it is expected to have only one video file
    # TODO be more intelligent to determine the file name
    downloaded_file_dir = pathlib.Path(os.getcwd())
    for f in downloaded_file_dir.glob('video.*'):
        video_file_path = f.resolve()
        break

    if remote_video_subtitle_lang is not None:
        reencode_downloaded_video()

    print(f'Downloaded video with file name: {video_file_path}')


def reencode_downloaded_video():
    print('The video needs re-encoding. This may take a long period of time.')
    run_binary('ffmpeg' , f'-i {video_file_path} -filter_complex subtitles={video_file_path}:force_style=\'Fontsize=28,OutlineColour=&H80000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=20\' video.mp4')


def extract_audio():
    print('//------------------------------ Extract the audio')
    # Extract the audio from the video
    run_binary('ffmpeg', f'-i {video_file_path} -q:a 0 -map a ./audio.wav')
    # Make the audio mono (and make it 32k)
    run_binary('sox', f'./audio.wav -c 1 -r 32000 ./32k-audio.wav')


def locate_speech_segments():
    print('//------------------------------ Extract the speech (heuristical)')
    with open(find_speech_log, 'w') as f:
        with redirect_stdout(f):
            find_speech.main([3, '32k-audio.wav'])


def collect_interesting_frames():
    # Collect the interesting frames
    print('//------------------------------ Collect the interesting frames (heuristical)')
    print('This may take a long period of time.')
    
    args = DummyArgs()
    args.input_video=video_file_path
    args.speech_time_log=find_speech_log
    args.time_interval = extract_frames_time_interval
    args.duration_secs = extract_video_frames.get_video_duration(video_file_path)

    extracted_frames_filenames, speech_timestampes_indexes = extract_video_frames.extract_main(args)

def downsample_frames():
    ## Downsample the images if necessary
    print('//------------------------------ Downsample the frames')
    print('This may take a long period of time.')
    path = pathlib.Path("./")
    for img in path.glob("*.jpg"):
        run_binary('convert', 
                f'{img} -crop {crop_width_pixel}x{crop_height_pixel}+{crop_x_offset}+{crop_y_offset} {img}')
        run_binary('convert', f'{img} -resize x{scaled_height_pixel} {img}')


def deduplicate_frames():
    print('//------------------------------ Deduplicate the frames (heuristical)')
    print('This may take a long period of time.')
    
    args = DummyArgs()
    args.width_pixel = int(scaled_width_pixel)
    args.height_pixel = int(scaled_height_pixel)
    args.upper_similarity_threshold = upper_similarity_threshold
    args.lower_similarity_threshold = lower_similarity_threshold
    args.use_subtitles=use_subtitles_to_deduplicate

    if not args.use_subtitles:
        print('Using fast deduplication method')
    else:
        print('Using probably more accurate deduplication method: comparing the subtitles detected')

    args.binary_thresholds = [i for i in range(250, 150, -20)] 

    file_pairs = deduplication.image_file_generator()
    deduplication.deduplication(args, file_pairs)


def generate_pptx():
    print('//------------------------------ Generate the pptx')
    print('This may take a long period of time if the number of slides > 1000.')

    args = DummyArgs()
    args.width_pixel = int(scaled_width_pixel)
    args.height_pixel = int(scaled_height_pixel)
    args.pixels_per_cm = pptx_pixels_per_cm 

    gen_pptx.main(args)

    pptx_file = pathlib.Path('story.pptx')
    if pptx_file.is_file():
        pptx_file.rename(f'{video_id}.pptx')


def config_video_dimensions():
    global width_pixel, height_pixel, crop_width_pixel, crop_height_pixel, scaled_width_pixel

    result = run_binary_and_get_stdout('ffprobe',
            f'-v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 {video_file_path}')
    frame_dimensions = result.split('x')
    frame_dimensions = [int(x.strip()) for x in frame_dimensions]

    width_pixel, height_pixel = frame_dimensions[0], frame_dimensions[1]

    if crop_width_pixel <= 0:
        # if the specified width of the cropped area <=0, it is set to the width of the video frame
        crop_width_pixel = width_pixel
    if crop_height_pixel <= 0:
        crop_height_pixel = height_pixel

    scaled_width_pixel=float(scaled_height_pixel)/height_pixel*width_pixel

    return frame_dimensions[0], frame_dimensions[1]


def main(args):
    global video_id, video_url, video_file_path
    global upper_similarity_threshold, lower_similarity_threshold
    global need_change_dir
    global crop_width_pixel, crop_height_pixel, crop_x_offset, crop_y_offset
    global remote_video_subtitle_lang
    global run_stages
    global width_pixel, height_pixel

    video_id = args.video_id
    if args.video_url is not None:
        video_url = args.video_url
    if args.local_video_path is not None:
        video_file_path = args.local_video_path
    upper_similarity_threshold = args.upper_similarity_threshold
    lower_similarity_threshold = args.lower_similarity_threshold
    need_change_dir = not args.no_need_change_dir
    crop_width_pixel = args.crop_width_pixel
    crop_height_pixel = args.crop_height_pixel
    crop_x_offet = args.crop_x_offet
    crop_y_offet = args.crop_y_offet
    if args.subtitle_lang is not None:
        remote_video_subtitle_lang=args.subtitle_lang
    run_stages = args.run_stages

    if need_change_dir:
        pathlib.Path.mkdir(pathlib.Path(video_id), parents=True, exist_ok=True)
        os.chdir(video_id)
        # everything we are doing will be inside {video_id}

    if RunStage.Download.value in run_stages:
        if video_url is not None:
            check_remote_video_subtitles()
            download_remote_video_and_set_local_path()

    width_pixel, height_pixel = config_video_dimensions()

    print('-' * 80)
    print('Video resolution:')
    print(f'  width {width_pixel} px height: {height_pixel} px')
    print(f'  crop: width {crop_width_pixel} px height: {crop_height_pixel} +x: {crop_x_offset} +y: {crop_y_offset} px')
    print(f'  scaled: width {scaled_width_pixel} px height: {scaled_height_pixel} px')
    print('-' * 80)


    if RunStage.LocateSpeechSegments.value in run_stages:
        extract_audio()
        locate_speech_segments()

    if RunStage.CollectFrames.value in run_stages:
        collect_interesting_frames()
        
    if RunStage.DownSampleFrames.value in run_stages:
        downsample_frames()

    if RunStage.DeduplicateFrames.value in run_stages:
        deduplicate_frames()

    if RunStage.GeneratePptx.value in run_stages:
        generate_pptx()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on existing video')
    parser.add_argument('--video_id', required=True, default=None,
            help='The ID of the video. Please use alphanumeric only.')

    parser_video_source = parser.add_mutually_exclusive_group(required=True)
    parser_video_source.add_argument('--local_video_path', required=False, default=None, 
            help='The local path to the video')
    parser_video_source.add_argument('--video_url', required=False, default=None, 
            help='The remote URL of the video')

    parser.add_argument('--upper_similarity_threshold', required=True, default=1, type=int,
            help='Similarity threshold of the upper portion')
    parser.add_argument('--lower_similarity_threshold', required=True, default=1, type=int,
            help='Similarity threshold of the lower portion')

    parser.add_argument('--no_need_change_dir', required=False, default=False, action='store_true',
            help='Whether the current directory has to be changed to the specified value')

    parser.add_argument('--crop_width_pixel', required=False, default=0, type=int,
            help='Width of the area to be cropped')
    parser.add_argument('--crop_height_pixel', required=False, default=0, type=int,
            help='Height of the area to be cropped')
    parser.add_argument('--crop_x_offet', required=False, default=0, type=int,
            help='Starting X coordinate of the cropping area')
    parser.add_argument('--crop_y_offet', required=False, default=0, type=int,
            help='Starting Y coordinate of the cropping area')

    parser.add_argument('--subtitle_lang', required=False, default=None,
            help='Please specify an available subtitle such as "zh-HK" of the video to be downloaded. Only effective for video_url')

    parser.add_argument('--run_stages', required=False, default=[
        RunStage.Download.value,
        RunStage.LocateSpeechSegments.value,
        RunStage.CollectFrames.value,
        RunStage.DownSampleFrames.value,
        RunStage.DeduplicateFrames.value,
        RunStage.GeneratePptx.value],
        help=f'Which stages should be executed? Please provide a space-separeted list of { [RunStage.Download.value, RunStage.LocateSpeechSegments.value, RunStage.CollectFrames.value, RunStage.DownSampleFrames.value, RunStage.DeduplicateFrames.value, RunStage.GeneratePptx.value] }')

    args = parser.parse_args()

    main(args)
