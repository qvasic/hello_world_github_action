#!/bin/sh -l

export PATH=$PATH:/style_police
export PYTHONPATH=/style_police

cd /github/workspace
python3 /style_police/check_commit_style.py ${1}
