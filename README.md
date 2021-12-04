# Video Summary

This is a project about producing a summary for the given video. The result is a series of images captured from the video that can sufficiently let the reader understand the whole story as if he is reading a comic book.

A rather simple heuristic is currently used to capture the interesting moments in the video: if someone speaks at a particular time, the video frames around that time are likely to be important. The code at this moment is the proof-of-concept of this idea.

## Dependencies

+ ffmpeg
+ img2pdf
+ sox
+ webrtcvad
+ youtube-dl
+ imagemagick
+ Tesseract
+ Tesseract-ocr language files for Chinese - Traditional
+ OpenCV
+ rq
+ flask
+ python-pptx
+ docker
+ docker-compose

# Installation
1. Build the base docker image of video-summarizer
    ```
    docker build -t video-summarizer . 
    ```
2. Build the images for docker-compose
    ```
    docker-compose -f ./docker-video-summarizer/docker-compose.yml build
    ```

## Usage
1. Start the docker images
    docker-compose -f ./docker-video-summarizer/docker-compose.yml up

2. Visit the API webpage to generate a .pptx file. The format is as follows:
    http://localhost:5000/enqueue/<string:video_id>/<path:video_url>/<int:upper_similarity_threshold>/<int:lower_similarity_threshold>/<string:preview_start_timestamp>/<string:preview_end_timestamp>

    e.g.  http://localhost:5000/enqueue/123/https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DfJubafP3IMI/20/20/00:00:00/00:00:00

## Utilities
The HTML and Javascript in record_screen can be used to record virtually everything on your desktop. Chrome supports recording both video and audio; on the other hand, Firefox seems to be able to record video only. 
