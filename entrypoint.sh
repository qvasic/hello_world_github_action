#!/bin/sh -l

export PATH=$PATH:/style_check
export PYTHONPATH=/style_check

cd /github/workspace
python3 /style_check/check_commit_style.py ${1}
