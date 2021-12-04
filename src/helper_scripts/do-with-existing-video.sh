#!/bin/bash

name=${1?ID of the video}
video_filename=${2?Video filename}
upper_similarity_threshold=${3? Similarity threshold of the upper portion}
lower_similarity_threshold=${4? Similarity threshold of the lower portion}
need_change_dir=${5-1}

scaled_height_pixel=270             # suppose we want the final frame to have height: 270 pixels (~ 4.7 cm when printed) #TODO

crop_width_pixel=0
crop_height_pixel=0
crop_x_offset=0
crop_y_offset=0

# Suggested values of the magic numbers to try:
#      if the frame:
#           is mostly static with some changing subtitles: 30, 10
#           has occasionally some static or slow-motion shots: 20, 10
#           change frequently: 7, 7
# The user needs to do experiments to get the best result

# Make a directory to store the files of this video
if [ "${need_change_dir}" == "1" ]
then
mkdir -p "$name"
cd "$name"
fi

video=${video_filename}

dimensions=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 ${video})

width_pixel=$(python -c "print('$dimensions'.split('x')[0])")
height_pixel=$(python -c "print('$dimensions'.split('x')[1])")
echo "Video resolution: ${dimensions}:"
echo "  width ${width_pixel} px height: ${height_pixel} px"

crop_width_pixel=$(python -c "print('${width_pixel}') if ${crop_width_pixel} == 0 else print('${crop_width_pixel}')")
crop_height_pixel=$(python -c "print('${height_pixel}') if ${crop_height_pixel} == 0 else print('${crop_height_pixel}')")
echo "  crop: width ${crop_width_pixel} px height: ${crop_height_pixel} +x: ${crop_x_offset} +y: ${crop_y_offset} px"

width_pixel=${crop_width_pixel}
height_pixel=${crop_height_pixel}

# scaled with respect to the height
scaled_width_pixel=$(python -c "print(int(${scaled_height_pixel}/${height_pixel}*${width_pixel}))")
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
python -u ../extract-video-frames.py --input_video ${video} --speech_time_log find-speech.log --time_interval 0.5


echo "//------------------------------ Downsample the frames"
# Downsample the images if necessary
for f in $(ls *.jpg)
do
  convert $f -crop ${crop_width_pixel}x${crop_height_pixel}+${crop_x_offset}+${crop_y_offset} $f
  convert $f -resize x${scaled_height_pixel} $f
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
