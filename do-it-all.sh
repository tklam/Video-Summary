#!/bin/bash

name=${1?}
url=${2?}

# Make a directory to store the files of this video
mkdir "$name"
cd "$name"

# Download the video
youtube-dl ${url} -o video


# Extract the audio from the video
ffmpeg -i video.* -q:a 0 -map a audio.wav
# Make the audio mono (and down-sample it)
sox audio.wav -c 1 -r 32000 32k-audio.wav 

# Locate the speech segments          
python -u ../find-speech.py 3 32k-audio.wav| tee find-speech.log

# Collect the interesting frames
python  ../extract-video-frames.py --input_video video.* --speech_time_log find-speech.log

# Downsample the images if necessary
for f in $(ls *.jpg)
do
  convert $f -resize 480x270 $f
done

# De-duplication (please adjust the parameters for every video)
python ../gen-pptx.py

# Combine the images and create the summary in the PDF format
# img2pdf $(ls -1v *.jpg) -o story.pdf
# mv story.pdf "${name}.pdf"

# Or, Combine the images and create the summary in the PPTX format
python ../gen-pptx.py
mv story.pptx "${name}.pptx"
