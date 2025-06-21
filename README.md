# 123av Video Downloader

A fast and efficient Python-based multithreaded downloader that uses an **unofficial API** to fetch segmented video streams (`.ts`) and merges them into a single `.mp4` video using FFmpeg.

It also supports downloading **videos that are split into multiple parts** (e.g., Part 1, Part 2, etc.) and automatically combines them into one seamless video.

## Features

- ✅ Uses an **unofficial API** to retrieve segment URLs  
- ⚡ Fast parallel downloading of `.ts` video segments for high-speed downloads  
- 🔁 Supports downloading **multi-part videos** as a single merged video  
- 🧠 Retry logic for failed downloads  
- 📉 Real-time download progress display  
- 🧹 Automatic cleanup of temporary files after merging  
- 📦 Merges all segments into one `.mp4` video using FFmpeg
