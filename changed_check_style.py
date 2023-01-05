#import sys
import diff_util
import unittest


def get_next_smaller_larger(value, iterable):
    """Returns next bigger and next smaller out from a set (any iterable).
    For instance iterable is [1, 2, 10, 12, 20, 55, 100],
    If value is 11, then result will be (10, 12).
    If value is 15, then result will be (12, 20).
    If value is 101, then result will be (100, None).
    If value is -1, then result will be (None, 1)."""

    if not iterable:
        return (None, None)

    data = set(iterable)
    data.add(value)
    sorted_data = list(sorted(data))
    position = sorted_data.index(value)
    
    if position == 0:
        return (None, sorted_data[1])

    if position == len(sorted_data)-1:
        return (sorted_data[-2], None)

    return (sorted_data[position-1], sorted_data[position+1])


def translate_line_numbers_onto_diff_for_github(line_number, map_data, do_translation):
    assert(map_data)

    if not do_translation:
        return line_number

    GITHUB_LINE_NUMBERS_OFFSET = -2

    if line_number in map_data:
        return map_data[line_number] + GITHUB_LINE_NUMBERS_OFFSET

    smaller, larger = get_next_smaller_larger(line_number, map_data.keys())

    if larger is not None:
        return map_data[larger] + GITHUB_LINE_NUMBERS_OFFSET

    if smaller is not None:
        return map_data[smaller] + GITHUB_LINE_NUMBERS_OFFSET

    return 1


def style_suggestions(a_b_diff, b_style_diff, use_github_diff_line_number=False):
    """Compares two diff a to b diff and b to style diff.
    Returns dict with line numbers as keys, and values are tuples with indeces:
    first start line from styled file, second - one-past-last, basically lines with 
    style suggestions.
    Basically suggests style changes only where original file was changed,
    does not suggest style changes where file wasn't touched.

    If use_github_diff_line_number is True, then instead of plain line number, they are 
    mapped onto diff, to be used in github comments."""

    changes_diff_data = diff_util.changed(a_b_diff)
    style_diff_data = diff_util.changed(b_style_diff)

    changes_changed_lines = set(changes_diff_data["changed_out"].keys())
    style_changed_lines = set(style_diff_data["changed_in"].keys())
    both_changed_lines = changes_changed_lines.intersection(style_changed_lines)
    style_changed_blocks = { style_diff_data["changed_in"][i] for i in both_changed_lines }

    suggestions = { translate_line_numbers_onto_diff_for_github(style_diff_data["blocks"][block]["in_start"], changes_diff_data["out"], use_github_diff_line_number)
                    : ( style_diff_data["blocks"][block]["out_start"], style_diff_data["blocks"][block]["out_start"] + style_diff_data["blocks"][block]["out_len"])
                          for block in style_changed_blocks }

    return suggestions


class TestChangedCheckStyle(unittest.TestCase):
    def test_get_next_smaller_larger(self):
        self.assertEqual(get_next_smaller_larger(10, []), (None, None))
        self.assertEqual(get_next_smaller_larger(10, [1, 2, 10, 12, 20, 55, 100]), (2, 12))
        self.assertEqual(get_next_smaller_larger(11, [1, 2, 10, 12, 20, 55, 100]), (10, 12))
        self.assertEqual(get_next_smaller_larger(15, [1, 2, 10, 12, 20, 55, 100]), (12, 20))
        self.assertEqual(get_next_smaller_larger(101, [1, 2, 10, 12, 20, 55, 100]), (100, None))
        self.assertEqual(get_next_smaller_larger(-11, [1, 2, 10, 12, 20, 55, 100]), (None, 1))

    def test_one(self):
        a_b_diff = ['--- wrongfully_formatted-a.cpp\t2022-12-15 20:02:47.780977200 +0200', '+++ wrongfully_formatted-b.cpp\t2022-12-15 20:03:35.891497500 +0200', '@@ -8,5 +8,5 @@', ' ', ' int main()', ' {', '-    return 0;', '+    return 1;', ' }']
        b_style_diff = ['--- wrongfully_formatted-b.cpp\t2022-12-15 20:03:35.891497500 +0200', '+++ -\t2022-12-21 13:18:48.962248900 +0200', '@@ -1,12 +1,8 @@', ' #include <iostream>', ' ', '-class A', '-{', '+class A {', ' public:', '-    A(){}', '+  A() {}', ' };', ' ', '-int main()', '-{', '-    return 1;', '-}', '+int main() { return 1; }']
        expected = {8: (7, 8)}
        actual = style_suggestions(a_b_diff, b_style_diff)
        self.assertEqual(actual, expected)


    def test_one_with_line_number_translation(self):
        a_b_diff = ['--- wrongfully_formatted-a.cpp\t2022-12-15 20:02:47.780977200 +0200', 
                    '+++ wrongfully_formatted-b.cpp\t2022-12-15 20:03:35.891497500 +0200', 
                    '@@ -8,5 +8,5 @@', 
                    ' ', 
                    ' int main()', 
                    ' {', 
                    '-    return 0;', 
                    '+    return 1;', 
                    ' }']
        b_style_diff = ['--- wrongfully_formatted-b.cpp\t2022-12-15 20:03:35.891497500 +0200', 
                        '+++ -\t2022-12-21 13:18:48.962248900 +0200', 
                        '@@ -1,12 +1,8 @@', 
                        ' #include <iostream>', 
                        ' ', 
                        '-class A', 
                        '-{', 
                        '+class A {', 
                        ' public:', 
                        '-    A(){}', 
                        '+  A() {}', 
                        ' };', 
                        ' ', 
                        '-int main()', 
                        '-{', 
                        '-    return 1;', 
                        '-}', 
                        '+int main() { return 1; }']
        expected = {2: (7, 8)}
        actual = style_suggestions(a_b_diff, b_style_diff, True)
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
