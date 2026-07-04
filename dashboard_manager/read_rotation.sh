#!/bin/sh
# Reads /config/dashboard_rotation.txt (one "Label | /path | seconds" entry
# per line -- human-readable, git-diff-friendly) and emits it as a single
# JSON object for command_line sensor.dashboard_rotation_text.
#
# Real newlines can't go raw inside a JSON string, so each line break is
# turned into a literal two-character `\n` escape (backslash + n) as the
# string is built; HA's JSON parser turns that back into a real newline
# when it decodes the sensor attribute. Uses only sh builtins (read/printf)
# since the HA core container isn't guaranteed to have sed/awk.
FILE="/config/dashboard_rotation.txt"
data=""
if [ -f "$FILE" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    if [ -z "$data" ]; then
      data="$line"
    else
      data="$data\\n$line"
    fi
  done < "$FILE"
fi
printf '{"data":"%s"}' "$data"
