import sys
import os

# Add the parent directory to sys.path to allow importing modules from it
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from _123AV import _123AV

'''
Run this script to download a 123AV video to the specified folder.
Change URL and output folder
'''

if __name__ == "__main__":
    app = _123AV()
    app.dl('https://123av.ws/ja/dm4/v/fc2-ppv-3266873', r'D:\DaikiVideos\123AV')