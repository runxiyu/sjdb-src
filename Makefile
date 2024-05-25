# A makefile again just because typing "make" feels more comfortable
# than typing "./auto.sh"

.PHONY: %

%:
	sh ./auto.sh $@
