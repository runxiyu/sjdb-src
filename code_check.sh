#!/bin/sh
mypy --strict .
pylint --disable C0301,W0511,C0114,C0115,C0116,R0913,R0914,C0209,W1201,E1205,R0915,R1728,W0613,C0200,R0912,R1702,E1101,W0621,R1718,R0801,W3101,W1514 *.py