#!/bin/bash

output=$(awk -F'[ =]' '/^alias / {print $2}' ~/.bash_aliases | rofi -dmenu -i)

[ -z "$output" ] && exit 0

bash -ic "$output"
