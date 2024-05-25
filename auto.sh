#!/bin/sh

set -x

if [ -z "$1" ]
then
	TARGET="$(date +"%Y-%m-%d")"
else
	TARGET="$1"
fi

if [ "$(date -d "$TARGET" +"%a")" = "Mon" ]
then
	python3 weekly.py --date="$TARGET"
fi

python3 daily.py --date="$TARGET"
python3 pack.py --date="$TARGET"
python3 sendmail.py --date="$TARGET"
