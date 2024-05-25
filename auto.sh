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
	python3 weekly.py --date="$TARGET" || exit 1
fi

python3 daily.py --date="$TARGET" || exit 2
python3 pack.py --date="$TARGET" || exit 3
python3 sendmail.py --date="$TARGET" || exit 4
