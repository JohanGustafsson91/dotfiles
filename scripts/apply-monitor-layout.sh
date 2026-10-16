#!/bin/sh

profile=${1:-}
connected=$(xrandr --query 2>/dev/null | awk '$2 == "connected" { print $1 }') || {
    notify-send 'Displays' 'Could not read connected monitors.'
    exit 1
}

has_output() {
    printf '%s\n' "$connected" | grep -Fxq "$1"
}

first_external=$(printf '%s\n' "$connected" | awk '$1 != "eDP-1" && NF { print; exit }')
second_external=$(printf '%s\n' "$connected" | awk '$1 != "eDP-1" && NF { count++; if (count == 2) print; exit }')
external_count=$(printf '%s\n' "$connected" | awk '$1 != "eDP-1" && NF { count++ } END { print count + 0 }')

primary=eDP-1
if ! has_output "$primary"; then
    primary=$(printf '%s\n' "$connected" | awk 'NF { print; exit }')
fi

case "$profile" in
    single)
        monitors=$primary
        ;;
    home-three)
        if [ "$external_count" -lt 2 ]; then
            notify-send 'Displays' 'Home layout requires two external monitors.'
            exit 1
        fi
        monitors="$primary $first_external $second_external"
        ;;
    auto)
        monitors=$connected
        ;;
    *)
        notify-send 'Displays' "Unknown monitor profile: $profile"
        exit 1
        ;;
esac

for output in $connected; do
    xrandr --output "$output" --off || {
        notify-send 'Displays' "Could not disable $output."
        exit 1
    }
done

previous=
for output in $monitors; do
    if [ -z "$previous" ]; then
        xrandr --output "$output" --primary --auto
    else
        xrandr --output "$output" --auto --right-of "$previous"
    fi

    if [ "$?" -ne 0 ]; then
        notify-send 'Displays' "Could not enable $output."
        exit 1
    fi
    previous=$output
done
