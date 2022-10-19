#!/bin/bash

output=$(cat ~/.bash_aliases | awk -F'[ =]' '{print $2}' | rofi -dmenu -i)
/bin/bash -i -c ${output}