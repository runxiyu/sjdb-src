.PHONY: tomorrow

TOMORROW != date '+%Y-%m-%d'

tomorrow:
	python3 daily.py --date=$(TOMORROW)
	python3 pack.py --date=$(TOMORROW)
	python3 send.py --date=$(TOMORROW)
