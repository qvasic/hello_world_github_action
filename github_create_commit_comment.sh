#!/bin/sh
if [ $# -ne 4 ]
then
    echo wrong number of arguments
    echo usage:
    echo $0 path position comment_body token
    exit 1
fi

curl -X POST -H "Accept: application/vnd.github+json" -H "Authorization: Bearer ${4}" -H "X-GitHub-Api-Version: 2022-11-28" https://api.github.com/repos/${GITHUB_REPOSITORY}/commits/${GITHUB_SHA}/comments -d "{\"path\":\"${1}\",\"position\":${2},\"body\":\"${3}\"}"
