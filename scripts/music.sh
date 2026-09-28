#!/bin/bash

if ! command -v playerctl >/dev/null 2>&1; then
    notify-send 'Music' 'Install playerctl to enable music controls.'
    exit 1
fi

# Prefer Spotify, then fall back to other MPRIS players.
player=(playerctl --player=spotify,%any)

action=${1:-menu}
if [ "$action" = menu ]; then
    choice=$(printf '%s\n' 'Play / Pause' 'Next track' 'Previous track' 'Stop' 'Open Spotify' |
        rofi -dmenu -i -p 'Music')
    case "$choice" in
        'Play / Pause') action=play-pause ;;
        'Next track') action=next ;;
        'Previous track') action=previous ;;
        Stop) action=stop ;;
        'Open Spotify') spotify >/dev/null 2>&1 & exit ;;
        *) exit ;;
    esac
fi

case "$action" in
    play-pause|next|previous|stop) "${player[@]}" "$action" >/dev/null 2>&1 ;;
    *) exit 1 ;;
esac
pkill -RTMIN+12 -x i3blocks
