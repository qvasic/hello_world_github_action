FROM python:3.8

WORKDIR /style_check
COPY entrypoint.sh /style_check/entrypoint.sh
COPY check_commit_style.py  style_config.yaml changed_check_style.py diff_util.py github_create_commit_comment.sh style_diff.sh /style_check/

ENTRYPOINT ["/entrypoint.sh"]
