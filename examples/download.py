import sys
import os

# Add the parent directory to sys.path to allow importing modules from it
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sub_processes.slow_123AV import _123AV

'''
Run this script to download a 123AV video to the specified folder.
Change URL and output folder
'''

if __name__ == "__main__":
    app = _123AV()
    app.dl('https://123av.com/en/v/fc2-ppv-4828384', r'D:\DaikiVideos\123AV')