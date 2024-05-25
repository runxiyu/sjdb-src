# Obviously this isn't the correct way to use Makefiles but it's the
# fastest for me to write

.PHONY: tomorrow %

TOMORROW != date '+%Y-%m-%d'

tomorrow:
	python3 daily.py --date=$(TOMORROW)
	python3 pack.py --date=$(TOMORROW)
	python3 sendmail.py --date=$(TOMORROW)

day-%:
	python3 daily.py --date=$@
	python3 pack.py --date=$@
	python3 sendmail.py --date=$@

week-%:
	python3 weekly.py --date=$@
