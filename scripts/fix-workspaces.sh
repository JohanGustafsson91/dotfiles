#!/bin/sh

move_to_workspace() {
    criteria=$1
    workspace=$2
    i3-msg "[$criteria] move container to workspace number $workspace" >/dev/null 2>&1
}

# Apply the generic rule first; specific apps below intentionally override it.
move_to_workspace 'class="Google-chrome"' 1
move_to_workspace 'instance="crx_bbdeiblfgdokhlblpgeaokenkfknecgl"' 3
move_to_workspace 'instance="chatgpt.com"' 6
move_to_workspace 'instance="crx_ompifgpmddkgmclendfeacglnodjjndh"' 9
move_to_workspace 'instance="crx_faolnafnngnfdaknnbpnkhgohbobgegn"' 8
move_to_workspace 'class="Slack"' 9
move_to_workspace 'class="Spotify"' 10

notify-send -u low -t 2500 'i3 workspaces' 'App workspaces fixed.' >/dev/null 2>&1 &
