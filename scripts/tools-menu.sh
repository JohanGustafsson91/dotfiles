#!/bin/sh

choice=$(printf '%s\n' \
    '󰉋  Project' \
    '󰂯  Bluetooth' \
    '󰘳  Fix app workspaces' \
    '󰍹  Single monitor' \
    '󰍹  Home · three monitors' \
    '󰍹  Office · two monitors' \
    '󰍺  Office · three monitors' \
    '󰍹  Auto-detect monitors' \
    '  Show clipboard' \
    '  Cancel' |
    rofi -dmenu -i -p 'Tools')

case "$choice" in
    *Project) alacritty --title 'Project' -e ~/.config/scripts/fuzzy-select-project.sh >/dev/null 2>&1 & ;;
    *Bluetooth) blueman-manager >/dev/null 2>&1 & ;;
    *'Fix app workspaces') ~/.config/scripts/fix-workspaces.sh ;;
    *'Single monitor') ~/.config/scripts/single-monitor.sh ;;
    *'Home · three monitors') ~/.config/scripts/home-three-monitors.sh ;;
    *'Office · two monitors') ~/.config/scripts/office-two-monitors.sh ;;
    *'Office · three monitors') ~/.config/scripts/office-three-monitors.sh ;;
    *'Auto-detect monitors') ~/.config/scripts/auto-monitors.sh ;;
    *'Show clipboard')
        clipboard=$(xclip -selection clipboard -o 2>/dev/null | head -c 500)
        [ -n "$clipboard" ] || clipboard='Clipboard is empty'
        notify-send 'Clipboard' "$clipboard"
        ;;
esac
