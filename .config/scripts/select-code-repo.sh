output=$(exec node ~/.config/scripts/list-code-repos.js ~/code | rofi -dmenu -i)
[ ! -z "$output" ] && cd "${HOME}/${output}" && code . && i3-sensible-terminal || exit 1