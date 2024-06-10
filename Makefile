# A makefile again just because typing "make" feels more comfortable
# than typing "./auto.sh"

.PHONY: % tomorrow

tomorrow:
	sh ./auto.sh $(shell date -d tomorrow '+%Y-%m-%d')

%:
	sh ./auto.sh $@
