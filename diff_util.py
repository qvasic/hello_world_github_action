import unittest
import re
import subprocess

def parse_git_diff_file_header(line):
    match = re.fullmatch( "diff --git a/(.+) b/(.+)", line )
    if match is None:
        raise ValueError("Malformed git diff file header: {line}".format(line = line))

    return match.groups()[1]


def parse_git_diff(git_diff):
    """Parses output of "git diff" command.
    Returns dict in following form: {file_path_name: changed_file_data}
    Where cahnged file data is: {"unidiff": list_of_lines_of_diff_for_that_file, 
                                 "deleted": flag_whether_file_was_deleted,
                                 "new_file": flag_whether_this_file_is_new,
                                 "renamed": flag_whether_this_file_was_renamed}"""

    i = 0
    parsed = {}
    while i < len(git_diff):


        if not git_diff[i].startswith("diff --git"):
            raise ValueError("Expected git diff file header.")
        filename = parse_git_diff_file_header(git_diff[i])
        i += 1

        deleted = False
        renamed = False
        new_file = False

        while i < len(git_diff) and not git_diff[i].startswith("diff --git") and not git_diff[i].startswith("index"):
            if git_diff[i].startswith("new file"):
                new_file = True
            elif git_diff[i].startswith("deleted file"):
                deleted = True
            elif git_diff[i].startswith("rename"):
                renamed = True
            i += 1

        if i < len(git_diff) and git_diff[i].startswith("index"):
            i += 1
            file_unidiff = []
            while i < len(git_diff) and not git_diff[i].startswith("diff --git"):
                file_unidiff.append(git_diff[i])
                i += 1

            parsed[filename] = { "unidiff": file_unidiff, "new_file": new_file, "deleted": deleted, "renamed": renamed }

    return parsed


def run(command, valid_return_codes=[0], ignore_return=False):
    r = subprocess.run(command, capture_output=True)
    if not ignore_return and r.returncode not in valid_return_codes:
        raise RuntimeError("Command {command} returned non-zero code: {code}".format(
            command=command, code=r.returncode))
    return r.stdout.decode()


def split_output(output):
    output = output.split("\n")
    if output[-1] == "":
        output.pop()
    return output


def diff(file_a, file_b):
    """Returns unidiff between file_a and file_b. Returns list of strings."""
    raw_unidiff = run(["diff", "-u", file_a, file_b], valid_return_codes=[0,1])
    return split_output(raw_unidiff)


def parse_hunk_header(line):
    match = re.fullmatch( "@@ \-(\d+),\d+ \+(\d+),\d+ @@.*", line )
    if match is None:
        raise ValueError("Malformed hunk header: {line}".format(line = line))

    return ( int(k)-1 for k in match.groups() )


def changed(diff):
    """Returns data about what was changed from a diff.
       Accepts unidiff (iterable of strings).
       Returns dict with following content:
       "changed_in": dict where keys are indeces of lines that  were changed in the "in" file, 
             values - index of a changed block this line belongs to
       "changed_out": the same, but for "out" file
       "blocks": list of dict, each of them contains:
           "in_start": first line of the block in the "in" file
           "in_len": length of the block in the "in" file
           "out_start": first line of the block in the "out" file
           "out_len": length of the block in the "out" file.
        "in": dict where keys are line number from "in" file that a mentioned in the diff (changed or not), 
              values - line number in the diff where it is mentioned
        "out": the same for "out" file."""

    result = {"changed_in": {}, "changed_out": {}, "blocks": [], "in": {}, "out": {}}

    if len(diff) == 0:
        return result

    if len(diff) < 3:
        raise ValueError("Too few lines in the diff.")
    if not diff[0].startswith("---"):
        raise ValueError("Expected line with in-file information.")
    if not diff[1].startswith("+++"):
        raise ValueError("Expected line with out-file information.")

    in_i, out_i = parse_hunk_header(diff[2])
    i = 2
    while i < len(diff):
        if diff[i].startswith(" "):
            result["in"][in_i] = i
            result["out"][out_i] = i
            in_i += 1
            out_i += 1
            i += 1
        elif diff[i].startswith("@@"):
            in_i, out_i = parse_hunk_header(diff[i])
            i += 1
        elif diff[i].startswith("-") or diff[i].startswith("+"):
            new_block = {"in_start": in_i, "in_len": 0, "out_start": out_i, "out_len": 0}
            while i < len(diff) and diff[i].startswith("-"):
                result["in"][in_i] = i
                result["changed_in"][in_i] = len(result["blocks"])
                in_i += 1
                new_block["in_len"] += 1
                i += 1
            while i < len(diff) and diff[i].startswith("+"):
                result["out"][out_i] = i
                result["changed_out"][out_i] = len(result["blocks"])
                out_i += 1
                new_block["out_len"] += 1
                i += 1
            result["blocks"].append(new_block)
        else:
            ValueError("Unexpected line prefix, line number: {line_number}".format(line_number = i))

    return result


class TestDiffUtil(unittest.TestCase):
    def test_empty(self):
        expected = {"changed_in": {}, "changed_out": {}, "blocks": [], "in": {}, "out": {}}
        self.assertEqual(changed([]), expected)
        self.assertEqual(changed(["---", "+++", "@@ -1,12 +1,13 @@"]), expected)

    def test_malformed_header(self):
        self.assertRaises(ValueError, changed, [""])
        self.assertRaises(ValueError, changed, ["1--", "+++", "@@ -1,12 +1,13 @@"])
        self.assertRaises(ValueError, changed, ["---", "1++", "@@ -1,12 +1,13 @@"])
        self.assertRaises(ValueError, changed, ["---", "+++"])

    def test_malformed_hunk_header(self):
        self.assertRaises(ValueError, changed, ["---", "+++", ""])
        self.assertRaises(ValueError, changed, ["---", "+++", "1@ -1,12 +1,13 @@"])
        self.assertRaises(ValueError, changed, ["---", "+++", "@@ -1, +1,13 @@"])
        self.assertRaises(ValueError, changed, ["---", "+++", "@@ -1,12 1,13 @@"])

    def test_diff_small(self):
        input = [ "--- a   2022-12-13 14:18:45.487729700 +0200",
                  "+++ b   2022-12-13 14:18:55.380516200 +0200",
                  "@@ -1,3 +1,3 @@",
                  " 0",
                  "-1",
                  "+11",
                  " 2" ]
        expected = {"changed_in": {1:0}, "changed_out": {1:0}, 
                    "blocks":[{"in_start": 1, "in_len": 1, "out_start": 1, "out_len": 1}],
                    "in": {0: 3, 1: 4, 2: 6}, "out": {0: 3, 1: 5, 2: 6}}
        self.assertEqual(changed(input), expected)

    def test_diff_even_smaller(self):
        input = [ "--- a   2022-12-13 14:18:45.487729700 +0200",
                  "+++ b   2022-12-13 14:18:55.380516200 +0200",
                  "@@ -1,1 +1,1 @@",
                  "-1",
                  "+11" ]
        expected = {"changed_in": {0:0}, "changed_out": {0:0}, 
                    "blocks":[{"in_start": 0, "in_len": 1, "out_start": 0, "out_len": 1}],
                    "in": {0: 3}, "out": {0: 4}}
        self.assertEqual(changed(input), expected)

    def test_diff_small_consecutive(self):
        input = [ "--- a   2022-12-13 14:18:45.487729700 +0200",
                  "+++ b   2022-12-13 14:18:55.380516200 +0200",
                  "@@ -1,3 +1,3 @@ what now",
                  " 0",
                  "-1",
                  "+11",
                  "-2",
                  "+22",
                  " 3" ]
        expected = {"changed_in": {1:0, 2:1}, "changed_out": {1:0, 2:1}, 
                    "blocks":[{"in_start": 1, "in_len": 1, "out_start": 1, "out_len": 1},
                              {"in_start": 2, "in_len": 1, "out_start": 2, "out_len": 1}],
                    "in": {0: 3, 1: 4, 2: 6, 3: 8}, "out": {0: 3, 1: 5, 2: 7, 3: 8}}
        self.assertEqual(changed(input), expected)

    def test_diff_big(self):
        self.maxDiff = None
        input = diff( "a", "b" )
        expected = {"changed_in": {2: 0, 3: 0, 6: 1, 24: 3}, "changed_out": {4: 1, 7: 2, 8: 2, 9: 2, 25: 3},
                    "blocks": [{"in_start": 2, "in_len": 2, "out_start": 2, "out_len": 0}, 
                               {"in_start": 6, "in_len": 1, "out_start": 4, "out_len": 1}, 
                               {"in_start": 9, "in_len": 0, "out_start": 7, "out_len": 3}, 
                               {"in_start": 24, "in_len": 1, "out_start": 25, "out_len": 1}, 
                              ],
                    "in": {0: 3, 1: 4, 2: 5, 3: 6, 4: 7, 5: 8, 6: 9, 7: 11, 8: 12, 9: 16, 10: 17, 11: 18,
                           21: 20, 22: 21, 23: 22, 24: 23, 25: 25},
                    "out": {0: 3, 1: 4, 2: 7, 3: 8, 4: 10, 5: 11, 6: 12, 7: 13, 8: 14, 9: 15, 10: 16, 11: 17, 12: 18,
                            22: 20, 23: 21, 24: 22, 25: 24, 26: 25}}
        self.assertEqual(changed(input), expected)

    def test_parse_git_diff_errors(self):
        self.assertRaises(ValueError, parse_git_diff, ["asdf"])
        self.assertRaises(ValueError, parse_git_diff, ["diff --git b/.github/workflows/test.yml a/.github/workflows/test.yml"])

    def test_parse_git_diff_empty(self):
        self.assertEqual(parse_git_diff(["diff --git a/.github/workflows/test.yml b/.github/workflows/test.yml", "index"]), 
                                        {".github/workflows/test.yml": { "unidiff": [], 
                                                                          "new_file": False, 
                                                                          "deleted": False, 
                                                                          "renamed": False }})

    def test_parse_git_diff_small(self):
        self.assertEqual(parse_git_diff([]), {})

    def test_parse_git_diff(self):
        input = [
            "diff --git a/.github/workflows/test.yml b/.github/workflows/test.yml",
            "index cb179e3..066ddb8 100644",
            "--- a/.github/workflows/test.yml",
            "+++ b/.github/workflows/test.yml",
            "@@ -15,8 +15,11 @@ jobs:",
            "           echo $GITHUB_WORKSPACE",
            "           echo {{ github.repository }}",
            "           echo hell0 world",
            "+",
            "+          # unit tests",
            "           python3 addition.py",
            "           python3 changed.py",
            "+",
            "           docker image ls",
            "           clang-format --version",
            "           echo $GITHUB_SHA",
            "diff --git a/changed.py b/changed.py",
            "index 1b906cf..3a26bdb 100644",
            "--- a/changed.py",
            "+++ b/changed.py",
            "@@ -3,6 +3,11 @@ import re",
            " import subprocess",
            "",
            "",
            "+def parse_git_diff(git_diff):",
            "+    pass",
            "+",
            "+",
            " def run(command, valid_return_codes=[0], ignore_return=False):",
            "     r = subprocess.run(command, capture_output=True)",
            "     if not ignore_return and r.returncode not in valid_return_codes:",
            "@@ -148,6 +153,14 @@ class TestChanged(unittest.TestCase):",
            "                               ]}",
            "         self.assertEqual(changed(input), expected)",
            "",
            "+    def test_parse_git_diff(self):",
            "+        input = [",
            "+",
            "+        ]",
            "+        actual = parse_git_diff(input)",
            "+        expected = {}",
            "+        self.assertEqual(actual, expected)",
            "+",
            "",
            " if __name__ == '__main__':",
            "     unittest.main()",
            "diff --git a/changed_check_style.py b/changed_check_style.py",
            "index d755c97..4f9fe22 100644",
            "--- a/changed_check_style.py",
            "+++ b/changed_check_style.py",
            "@@ -3,11 +3,14 @@ import changed",
            "     changes_unidiff = changed.diff(base, changes)",
            "",
            "-    changes_diff_data = changed.changed(changes_unidiff)",
            "+    changes_diff_data =  changed.changed(changes_unidiff)",
            "     style_diff_data = changed.changed(style_unidiff)",
        ]
        actual = parse_git_diff(input)
        expected = {".github/workflows/test.yml": { "unidiff": [
                                                        "--- a/.github/workflows/test.yml",
                                                        "+++ b/.github/workflows/test.yml",
                                                        "@@ -15,8 +15,11 @@ jobs:",
                                                        "           echo $GITHUB_WORKSPACE",
                                                        "           echo {{ github.repository }}",
                                                        "           echo hell0 world",
                                                        "+",
                                                        "+          # unit tests",
                                                        "           python3 addition.py",
                                                        "           python3 changed.py",
                                                        "+",
                                                        "           docker image ls",
                                                        "           clang-format --version",
                                                        "           echo $GITHUB_SHA" ], 
                                                    "new_file": False, 
                                                    "deleted": False, 
                                                    "renamed": False },
                    "changed.py": { "unidiff": [
                                        "--- a/changed.py",
                                        "+++ b/changed.py",
                                        "@@ -3,6 +3,11 @@ import re",
                                        " import subprocess",
                                        "",
                                        "",
                                        "+def parse_git_diff(git_diff):",
                                        "+    pass",
                                        "+",
                                        "+",
                                        " def run(command, valid_return_codes=[0], ignore_return=False):",
                                        "     r = subprocess.run(command, capture_output=True)",
                                        "     if not ignore_return and r.returncode not in valid_return_codes:",
                                        "@@ -148,6 +153,14 @@ class TestChanged(unittest.TestCase):",
                                        "                               ]}",
                                        "         self.assertEqual(changed(input), expected)",
                                        "",
                                        "+    def test_parse_git_diff(self):",
                                        "+        input = [",
                                        "+",
                                        "+        ]",
                                        "+        actual = parse_git_diff(input)",
                                        "+        expected = {}",
                                        "+        self.assertEqual(actual, expected)",
                                        "+",
                                        "",
                                        " if __name__ == '__main__':",
                                        "     unittest.main()" ], 
                                    "new_file": False, 
                                    "deleted": False, 
                                    "renamed": False },
                    "changed_check_style.py": { "unidiff": [
                                    "--- a/changed_check_style.py",
                                    "+++ b/changed_check_style.py",
                                    "@@ -3,11 +3,14 @@ import changed",
                                    "     changes_unidiff = changed.diff(base, changes)",
                                    "",
                                    "-    changes_diff_data = changed.changed(changes_unidiff)",
                                    "+    changes_diff_data =  changed.changed(changes_unidiff)",
                                    "     style_diff_data = changed.changed(style_unidiff)" ], 
                                                "new_file": False, 
                                                "deleted": False, 
                                                "renamed": False }
        }

        self.assertEqual(actual, expected)

    def test_parse_git_diff_with_changed_files(self):
        input = [
            "diff --git a/wrongfully_formatted-b.cpp b/wrongfully_formatted-b.cpp",
            "new file mode 100644",
            "index 0000000..e69de29",
            "diff --git a/wrongfully_formatted-a.cpp b/wrongfully_formatted-c.cpp",
            "similarity index 100%",
            "rename from wrongfully_formatted-a.cpp",
            "rename to wrongfully_formatted-c.cpp",
            "diff --git a/wrongfully_formatted-d.cpp b/wrongfully_formatted-d.cpp",
            "deleted file mode 100644",
            "index af5846b..0000000",
            "--- a/wrongfully_formatted-d.cpp",
            "+++ /dev/null",
            "@@ -1,12 +0,0 @@",
            "-#include <iostream>",
            "-",
            "-class A",
            "-{",
            "-public:",
            "-    A(){}",
            "-};",
            "-",
            "-int main()",
            "-{",
            "-    return 1;",
            "-}"
        ]
        actual = parse_git_diff(input)
        expected = {"wrongfully_formatted-b.cpp": { "unidiff": [], 
                                                    "new_file": True, 
                                                    "deleted": False, 
                                                    "renamed": False },
                    "wrongfully_formatted-d.cpp": { "unidiff": [
                                                    "--- a/wrongfully_formatted-d.cpp",
                                                    "+++ /dev/null",
                                                    "@@ -1,12 +0,0 @@",
                                                    "-#include <iostream>",
                                                    "-",
                                                    "-class A",
                                                    "-{",
                                                    "-public:",
                                                    "-    A(){}",
                                                    "-};",
                                                    "-",
                                                    "-int main()",
                                                    "-{",
                                                    "-    return 1;",
                                                    "-}" ], 
                                                "new_file": False, 
                                                "deleted": True, 
                                                "renamed": False }
        }

        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
