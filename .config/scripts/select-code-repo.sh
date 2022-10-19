output=$(exec node ~/.config/scripts/list-code-repos.js ~/code | rofi -dmenu -i)
[ ! -z "$output" ] && exec code "${HOME}/${output}" || exit 1