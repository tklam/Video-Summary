# Video Summary

This is a project about producing a summary for the given video. The result is a series of images captured from the video that can sufficiently let the reader understand the whole story as if he is reading a comic book.

A rather simple heuristic is currently used to capture the interesting moments in the video: if someone speaks at a particular time, the video frames around that time are likely to be important. The code at this moment is the proof-of-concept of this idea.

## Dependencies

+ ffmpeg
+ img2pdf
+ sox
+ webrtcvad
+ youtube-dl

## Usage
Suppose we want to produce a summary of
[試映劇場《寫實的天能》完整版｜試當真](https://www.youtube.com/watch?v=pumhdhv6r2w), please follow the steps listed below:

```
# Make a directory to store the files of this video
mkdir "試映劇場《寫實的天能》完整版｜試當真"
cd "試映劇場《寫實的天能》完整版｜試當真"

# Download the video
youtube-dl https://www.youtube.com/watch\?v\=pumhdhv6r2w -o video


# Extract the audio from the video
ffmpeg -i video.mp4 -q:a 0 -map a audio.wav
# Make the audio mono (and down-sample it)
sox audio.wav -c 1 -r 32000 32k-audio.wav 

# Locate the speech segments          
python ../find-speech.py 3 32k-audio.wav| tee find-speech.log

# Collect the interesting frames
python  ../extract-video-frames.py --input_video video.mp4 --speech_time_log find-speech.log

# Combine the images and create the summary in the PDF format
img2pdf $(ls -1v *.jpg) -o story.pdf

# Or, Combine the images and create the summary in the PPTX format
python ../gen-pptx.py
```
