#!/bin/sh

choice=$(printf '%s\n' \
    '  Lock' \
    '󰤄  Suspend' \
    '󰑐  Reload i3' \
    '󰑓  Restart i3' \
    '  Audio settings' \
    '󰤨  Network (nmtui)' \
    '  Screenshot' \
    '  Cancel' |
    rofi -dmenu -i -p 'System')

case "$choice" in
    *Lock) ~/.config/scripts/lockscreen.sh ;;
    *Suspend) systemctl suspend ;;
    *'Reload i3') i3-msg reload ;;
    *'Restart i3') i3-msg restart ;;
    *'Audio settings') pavucontrol >/dev/null 2>&1 & ;;
    *'Network (nmtui)') alacritty --config-file ~/.config/alacritty/nmtui.toml --title 'Network' -e nmtui >/dev/null 2>&1 & ;;
    *Screenshot) flameshot gui ;;
esac
