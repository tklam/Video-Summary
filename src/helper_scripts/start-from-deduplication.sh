#!/bin/bash

name=${1?ID of the video}
video_filename=${2?Video filename}
upper_similarity_threshold=${3? Similarity threshold of the upper portion}
lower_similarity_threshold=${4? Similarity threshold of the lower portion}
scaled_height_pixel=270             # suppose we want the final frame to have height: 270 pixels (~ 4.7 cm when printed) #TODO

# Suggested values of the magic numbers to try:
#      if the frame:
#           is mostly static with some changing subtitles: 30, 10
#           has occasionally some static or slow-motion shots: 20, 10
#           change frequently: 7, 7
# The user needs to do experiments to get the best result

# Make a directory to store the files of this video
mkdir -p "$name"
cd "$name"

video=${video_filename}

dimensions=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 ${video})

width_pixel=$(python -c "print('$dimensions'.split('x')[0])")
height_pixel=$(python -c "print('$dimensions'.split('x')[1])")

# scaled with respect to the height
scaled_width_pixel=$(python -c "print(int(${scaled_height_pixel}/${height_pixel}*${width_pixel}))")
echo "Video resolution: ${dimensions}:"
echo "  width ${width_pixel} px height: ${height_pixel} px"
echo "  scaled: width ${scaled_width_pixel} px height: ${scaled_height_pixel} px"



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
