#!/bin/bash

name=${1?ID of the video}
url=${2?Url of the video}
subtitle_lang=${3?none, or an available subtitle such as zh-HK}
upper_similarity_threshold=${4? Similarity threshold of the upper portion}
lower_similarity_threshold=${5? Similarity threshold of the lower portion}

# Suggested values of the magic numbers to try:
#      if the frame:
#           is mostly static with some changing subtitles: 30, 10
#           has occasionally some static or slow-motion shots: 20, 10
#           change frequently: 7, 7
# The user needs to do experiments to get the best result

# Make a directory to store the files of this video
mkdir -p "$name"
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
  video=$(ls video.* | tail -n 1)
  echo "Video file name: ${video}"

  echo "The video needs re-encoding. This may take a long period of time."
  ffmpeg -i ${video} -filter_complex "subtitles=${video}:force_style='Fontsize=28,OutlineColour=&H80000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=20'" video.mp4

fi

echo "Downloaded video"

../do-with-existing-video.sh ${name} ${video} ${upper_similarity_threshold} ${lower_similarity_threshold} 0
