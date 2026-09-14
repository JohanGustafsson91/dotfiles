#!/bin/bash

selected_session=$(tmux list-sessions -F "#{session_name}" | fzf --prompt="Select session to kill: ")

if [[ -z "$selected_session" ]]; then
  echo "No session selected"
  exit 1
fi

tmux kill-session -t "$selected_session"
echo "Session '$selected_session' killed."
