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

## Usage
Suppose we want to produce a summary of
[試映劇場《寫實的天能》完整版｜試當真](https://www.youtube.com/watch?v=pumhdhv6r2w), please do:

```
./do-it-all.sh \
  '試映劇場《寫實的天能》完整版｜試當真' \
  'none'
  https://www.youtube.com/watch?v=pumhdhv6r2w \
  25 25

  # 'none' indicates that the video has no subtitle. If there are some subtitles, the user can provide the subtitles's ISO code, such as 'zh-HK' .
  # 25 25 are some magic numbers for frame deduplication, please refer to the comments in do-it-all.sh
```

If the magic numbers are inappropriate, we can start from the deduplication step and try using another
set of parameters.

Alternatively, we can make use of batch.py.
