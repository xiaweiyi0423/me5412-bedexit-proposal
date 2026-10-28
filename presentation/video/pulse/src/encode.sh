#!/bin/bash
# frames/f%04d.png + music.wav -> pulse.mp4 (1080p30, -14 LUFS)
cd "$(dirname "$0")"
ffmpeg -v error -y -framerate 30 -i frames/f%04d.png -i music.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -af "loudnorm=I=-14:TP=-1.0:LRA=9" -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart pulse.mp4
