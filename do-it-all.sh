#!/bin/bash

name=${1?}
url=${2?}
subtitle_lang=${3?}
upper_similarity_threshold=${4?}
lower_similarity_threshold=${5?}
scaled_height_pixel=270             # suppose we want the final frame to have height: 270 pixels (~ 4.7 cm when printed) #TODO

# Suggested values of the magic numbers to try:
#      if the frame:
#           is mostly static with some changing subtitles: 30, 10
#           has occasionally some static or slow-motion shots: 20, 10
#           change frequently: 7, 7
# The user needs to do experiments to get the best result

# Make a directory to store the files of this video
mkdir "$name"
cd "$name"

# Download the video
# list the available subtitles
echo "//------------------------------ List of subtitles available"
youtube-dl --list-subs --skip-download ${url}

echo "//------------------------------ Download the video"
if [ "${subtitle_lang}" == "none" ]
then
  # no subitle
  youtube-dl ${url} -o video
  video=$(ls video.*) # it is expected to have only one video file
  echo "Video file name: ${video}"

else
  youtube-dl --embed-subs --write-sub --convert-subtitles srt --sub-lang ${subtitle_lang}  ${url} -o video
  video=$(ls video.*) # it is expected to have only one video file
  echo "Video file name: ${video}"

  echo "The video needs re-encoding. This may take a long period of time."
  ffmpeg -i ${video} -filter_complex "subtitles=${video}:force_style='Fontsize=28,OutlineColour=&H80000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=20'" video.mp4

fi


dimensions=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 ${video})

width_pixel=$(python -c "print('$dimensions'.split('x')[0])")
height_pixel=$(python -c "print('$dimensions'.split('x')[1])")

# scaled with respect to the height
scaled_width_pixel=$(python -c "print(int(${scaled_height_pixel}/${height_pixel}*${width_pixel}))")
echo "Video resolution: ${dimensions}:"
echo "  width ${width_pixel} px height: ${height_pixel} px"
echo "  scaled: width ${scaled_width_pixel} px height: ${scaled_height_pixel} px"


echo "//------------------------------ Extract the audio"
# Extract the audio from the video
ffmpeg -i ${video} -q:a 0 -map a audio.wav
# Make the audio mono (and down-sample it)
sox audio.wav -c 1 -r 32000 32k-audio.wav 


# Locate the speech segments          
echo "//------------------------------ Extract the speech (heuristical)"
python -u ../find-speech.py 3 32k-audio.wav| tee find-speech.log


# Collect the interesting frames
echo "//------------------------------ Collect the interesting frames (heuristical)"
echo "This may take a long period of time."
python -u ../extract-video-frames.py --input_video ${video} --speech_time_log find-speech.log


echo "//------------------------------ Downsample the frames"
# Downsample the images if necessary
for f in $(ls *.jpg)
do
  convert $f -resize ${scaled_width_pixel}x${scaled_height_pixel} $f
done


# De-duplication (please adjust the parameters for every video)
echo "//------------------------------ Deduplicate the frames (heuristical)"
python -u ../deduplication.py \
  --width_pixel ${scaled_width_pixel} --height_pixel ${scaled_height_pixel} \
  --upper_similarity_threshold ${upper_similarity_threshold} \
  --lower_similarity_threshold ${lower_similarity_threshold}


# Combine the images and create the summary in the PDF format
# img2pdf $(ls -1v *.jpg) -o story.pdf
# mv story.pdf "${name}.pdf"


# Or, Combine the images and create the summary in the PPTX format
echo "//------------------------------ Generate the pptx"
echo "This may take a long period of time if the number of slides > 1000."
python -u ../gen-pptx.py \
  --width_pixel ${scaled_width_pixel} --height_pixel ${scaled_height_pixel}


echo "//------------------------------ Final rename"
mv story.pptx "${name}.pptx"

# If we want to OCR the rendered subtitles (slow)
# echo "//------------------------------ OCR subtitles"
# python -u ../capture_subtitle.py --x0 0 --x1 480 --y0 200 --y1 270 --is_white_subtitle | tee subtitle.txt
