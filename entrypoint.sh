#!/bin/sh -l

echo "Hello ${1}"

pwd
ls
git --version
ls /github/workspace
cd /github/workspace
git diff HEAD~1
