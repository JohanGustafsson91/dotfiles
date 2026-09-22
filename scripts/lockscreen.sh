#!/bin/bash
icon="$HOME/.config/i3/lock.png"
# create a temp file
img=$(mktemp /tmp/XXXXXXXXXX.png)
# Take a screenshot of current desktop
import -window root $img 
# Pixelate the screenshot
size=$(identify -format '%wx%h' "$img")
convert "$img" -scale 15.3846% -scale "$size!" "$img"
# Alternatively, blur the screenshot (slow!)
#convert $img -blur 2,5 $img
# Add the lock image
convert $img $icon -gravity center -composite $img
# Run i3lock with custom background
i3lock -i $img
# Remove the tmp file
rm $img
