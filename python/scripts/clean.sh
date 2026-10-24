#!/usr/bin/env sh
here="$(cd "$(dirname "$0")" && pwd)"
if command -v python3 >/dev/null 2>&1; then py=python3; else py=python; fi
"$py" "$here/../tools/clean.py" "$@"
rc=$?
printf "Press any key to continue..."
old=$(stty -g 2>/dev/null) && stty -icanon -echo min 1 time 0
dd bs=1 count=1 >/dev/null 2>&1
[ -n "$old" ] && stty "$old"
echo
exit $rc
