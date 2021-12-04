# For Windows users and people who are new to Python

You can run Video Summary script with WSL (Windows Subsystem For Linux). If you are not familiar with Linux, you can start with WSL2 and Ubuntu (other Linux should work but I haven't tried). The following is written for Ubuntu-based distributions. This [guide](https://docs.microsoft.com/en-us/windows/wsl/install-win10) will show you how you can install WSL2 and get Ubuntu from [Microsoft Store](https://www.microsoft.com/store/apps/9n6svws3rx71).

After you installed WSL with your favourite Linux distribution, you can check the version of your Python install with:

        python --version

This script requires Python 3.7 or above to run. If you need to install Python3, the command is:

        sudo apt-get install python3

## install required tools

Our script use youtube-dl to download videos. You can install with:

        sudo curl -L https://yt-dl.org/downloads/latest/youtube-dl -o /usr/local/bin/youtube-dl
        sudo chmod a+x /usr/local/bin/youtube-dl

There are more tools required to run the script. You can install them with:

        sudo apt-get install ffmpeg imagemagick sox 

and some python libraries:

        pip install webrtcvad sox numpy python-pptx imagehash image opencv-python img2pdf

## Access your files from Windows 

You can use Windows Explorer and type \\wsl$ and access the file system in Linux. By default, your work shall be found under \home\<your username> folder.
