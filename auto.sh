#!/bin/sh

if [ -z "$1" ]
then
	TARGET="$(date +"%Y-%m-%d")"
else
	TARGET="$1"
fi
printf 'Target: %s\n' "$TARGET"

if [ "$(date -d "$TARGET" +"%a")" = "Sun" ] || [ "$(date -d "$TARGET" +"%a")" = "Sat" ]
then
	printf 'Not generating for weekends, exiting\n' >&2
	exit 5
fi

if [ "$(date -d "$TARGET" +"%a")" = "Mon" ]
then
	printf 'Target day is a Monday, running weekly.py too\n' >&2
	python3 weekly.py --date="$TARGET" || exit 1
fi

printf 'Running daily.py\n' >&2
python3 daily.py --date="$TARGET" || exit 2
printf 'Running pack.py\n' >&2
python3 pack.py --date="$TARGET" || exit 3
printf 'Running sendmail.py\n' >&2
python3 sendmail.py --date="$TARGET" || exit 4
