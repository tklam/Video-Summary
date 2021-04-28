import os
import sys
import subprocess

pending = {
1:	'https://www.youtube.com/watch?v=857_DiQACqM'
}

for id, url in pending.items():
    p = subprocess.run(['./do-it-all.sh'] + f'{id} {url}'.split())
    if p.returncode != 0:
        print(f'An error occurred when processing video: {id}')
