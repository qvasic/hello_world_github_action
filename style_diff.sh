#!/bin/sh
if [ $# -lt 2 ]
then
    echo wrong number of arguments
    echo usage:
    echo $0 file style_checker [optional style arguments]
    exit 1
fi
$2 $3 $4 $5 $6 $7 $8 $9 ${10} ${11} ${12} ${13} ${14} ${15} ${16} ${17} ${18} ${19} ${20} $1 | diff -u $1 -
