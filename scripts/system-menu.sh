#!/bin/sh

choice=$(printf '%s\n' \
    '  Lock' \
    '󰤄  Suspend' \
    '  Shutdown' \
    '󰗼  Logout' \
    '󰑐  Reload i3' \
    '󰑓  Restart i3' \
    '  Audio settings' \
    '♪  Music' \
    '☀  Väder Trollhättan (klart.se)' \
    '☀  Väder Göteborg (klart.se)' \
    '󰤨  Network (nmtui)' \
    '  Screenshot' \
    '󰉋  Project' \
    '󰂯  Bluetooth' \
    '󰘳  Fix app workspaces' \
    '󰍹  Single monitor' \
    '󰍹  Home · three monitors' \
    '󰍺  Office · three monitors' \
    '󰍹  Auto-detect monitors' \
    '  Show clipboard' \
    '  Cancel' |
    rofi -dmenu -i -p 'System')

confirm() {
    [ "$(printf 'No\nYes\n' | rofi -dmenu -i -p "$1")" = 'Yes' ]
}

case "$choice" in
    *Lock) ~/.config/scripts/lockscreen.sh ;;
    *Suspend) confirm 'Suspend?' && systemctl suspend ;;
    *Shutdown) confirm 'Shutdown?' && systemctl poweroff ;;
    *Logout) confirm 'Logout?' && i3-msg exit ;;
    *'Reload i3') i3-msg reload ;;
    *'Restart i3') i3-msg restart ;;
    *'Audio settings') pavucontrol >/dev/null 2>&1 & ;;
    *Music) ~/.config/scripts/music.sh ;;
    *'Väder Trollhättan (klart.se)') xdg-open "https://www.klart.se/se/v%C3%A4stra-g%C3%B6talands-l%C3%A4n/v%C3%A4der-trollh%C3%A4ttan/j%C3%A4mf%C3%B6r/#$(TZ=Europe/Stockholm date +%F)" >/dev/null 2>&1 & ;;
    *'Väder Göteborg (klart.se)') xdg-open "https://www.klart.se/se/v%C3%A4stra-g%C3%B6talands-l%C3%A4n/v%C3%A4der-g%C3%B6teborg/j%C3%A4mf%C3%B6r/#$(TZ=Europe/Stockholm date +%F)" >/dev/null 2>&1 & ;;
    *'Network (nmtui)') alacritty --config-file ~/.config/alacritty/nmtui.toml --title 'Network' -e nmtui >/dev/null 2>&1 & ;;
    *Screenshot) flameshot gui ;;
    *Project) alacritty --title 'Project' -e ~/.config/scripts/fuzzy-select-project.sh >/dev/null 2>&1 & ;;
    *Bluetooth) blueman-manager >/dev/null 2>&1 & ;;
    *'Fix app workspaces') ~/.config/scripts/fix-workspaces.sh ;;
    *'Single monitor') ~/.config/scripts/single-monitor.sh ;;
    *'Home · three monitors') ~/.config/scripts/home-three-monitors.sh ;;
    *'Office · three monitors') ~/.config/scripts/office-three-monitors.sh ;;
    *'Auto-detect monitors') ~/.config/scripts/auto-monitors.sh ;;
    *'Show clipboard')
        clipboard=$(xclip -selection clipboard -o 2>/dev/null | head -c 500)
        [ -n "$clipboard" ] || clipboard='Clipboard is empty'
        notify-send 'Clipboard' "$clipboard"
        ;;
esac
