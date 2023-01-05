import diff_util
import changed_check_style
import sys
import yaml


configuration = {'c-like': 
                    {'suffixes': ['.c', '.h', '.cpp', '.hpp', '.hxx'], 
                     'styler_command': ['clang-format']}
                }


def load_configuration():
    with open("style_config.yaml") as config_file:
        yaml_object = yaml.load(config_file, yaml.Loader)
    
    if "style_config" not in yaml_object or type(yaml_object["style_config"]) is not dict:
        raise RuntimeError("Style configuration error.")

    style_config = yaml_object["style_config"]

    for style_class in style_config:
        if "suffixes" not in style_config[style_class] or type(style_config[style_class]["suffixes"]) is not list:
            raise RuntimeError("Style configuration error.")

        if "styler_command" not in style_config[style_class] or type(style_config[style_class]["styler_command"]) is not list:
            raise RuntimeError("Style configuration error.")

    global configuration
    configuration = style_config


def check_changed_style(file, diff, styler, report_style_suggestion):
    styled_file = diff_util.split_output(diff_util.run(styler + [file]))
    style_unidiff = diff_util.split_output(diff_util.run(["sh", "style_diff.sh", file] + styler, valid_return_codes=[0, 1]))

    suggestions = changed_check_style.style_suggestions(diff, style_unidiff, True)

    if not suggestions:
        return False

    for line in suggestions:
        styled_suggestion = "\\n".join(styled_file[suggestions[line][0] : suggestions[line][1]])
        report_style_suggestion(file, line, styled_suggestion)

    return True


def main(github_token):
    load_configuration()

    commit_diff = diff_util.split_output(diff_util.run(["git", "diff", "HEAD~1"]))
    commit_changed_files = diff_util.parse_git_diff(commit_diff)

    any_suggestions = False

    def report_style_suggestions(file, line, suggestion):
        print("file {}, line {}:".format(file, line+1))
        print(suggestion)

        if github_token is not None:
            diff_util.run(["sh", "github_create_commit_comment.sh", file, str(line), "Suggested formatting:\\n".format(line + 1) + "```\\n" + suggestion + "\\n```", github_token])

    for changed_file in commit_changed_files:

        for style_class in configuration:
            for suffix in configuration[style_class]["suffixes"]:
                if changed_file.endswith(suffix):
                    if check_changed_style(changed_file, commit_changed_files[changed_file]["unidiff"], configuration[style_class]["styler_command"], report_style_suggestions):
                        any_suggestions = True
                    continue

    if any_suggestions:
        exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("usage:\n\t{cmd} [github_token]".format(cmd=sys.argv[0]))
        exit(1)

    if len(sys.argv) < 2:
        main(None)
    else:
        main(sys.argv[1])
