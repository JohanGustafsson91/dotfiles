#!/bin/sh

choice=$(printf '%s\n' \
    '󰉋  Project' \
    '󰂯  Bluetooth' \
    '󰍹  Two screens' \
    '󰍺  Three screens' \
    '  Show clipboard' \
    '  Cancel' |
    rofi -dmenu -i -p 'Tools')

case "$choice" in
    *Project) alacritty --title 'Project' -e ~/.config/scripts/fuzzy-select-project.sh >/dev/null 2>&1 & ;;
    *Bluetooth) blueman-manager >/dev/null 2>&1 & ;;
    *'Two screens') ~/.config/scripts/display-two-screens.sh ;;
    *'Three screens') ~/.config/scripts/display-three-screens.sh ;;
    *'Show clipboard')
        clipboard=$(xclip -selection clipboard -o 2>/dev/null | head -c 500)
        [ -n "$clipboard" ] || clipboard='Clipboard is empty'
        notify-send 'Clipboard' "$clipboard"
        ;;
esac
