FROM python:3.8
RUN python3 -m pip install pyyml

WORKDIR /style_police
COPY entrypoint.sh /style_police/entrypoint.sh
COPY check_commit_style.py style_config.yaml changed_check_style.py diff_util.py github_create_commit_comment.sh style_diff.sh /style_police/

ENTRYPOINT ["/style_police/entrypoint.sh"]
