import os
import sys
import subprocess

pending = {
# Format:
#      id: (
#             url,
#             subtitle language: none or en/zh-HK,
#             magic number for frame deduplication (frame body),
#             magic number for frame deduplication (frame subtitle)
#           )
#
# Suggested values of the magic numbers to try:
#      if the frame:
#           is mostly static with some changing subtitles: 30, 10
#           has occasionally some static or slow-motion shots: 20, 10
#           change frequently: 7, 7
# The user needs to do experiments to get the best result
'1' :   ('https://www.youtube.com/watch?v=YI4qsJhZtwA', 'none', 25, 25),
'2' :   ('https://www.youtube.com/watch?v=YI4qsJhZtwA', 'zh-HK', 25, 25)
}

for id, video_info in pending.items():
    url, subtitle_lang, upper_similarity_threshold, lower_similarity_threshold = video_info
    p = subprocess.run(['./do-it-all.sh'] + 
        f'{id} {url} {subtitle_lang} {upper_similarity_threshold} {lower_similarity_threshold}'.split())
    if p.returncode != 0:
        print(f'An error occurred when processing video: {id}')
