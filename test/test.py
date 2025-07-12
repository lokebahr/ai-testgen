import pytest
from function import moving_average

def test_non_list_nums_input():
    with pytest.raises(TypeError):
        moving_average("not a list", 3)

def test_non_integer_window_input():
    with pytest.raises(TypeError):
        moving_average([1, 2, 3], "3")

def test_positive_window_value():
    with pytest.raises(ValueError):
        moving_average([1, 2, 3], -1)

def test_window_larger_than_nums_length():
    with pytest.raises(ValueError):
        moving_average([1, 2, 3], 5)

def test_off_by_one_range_issue():
    assert moving_average([1, 2, 3, 4, 5], 3) == [2.0, 3.0, 4.0]

def test_valid_input_expected_output():
    assert moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]

def test_empty_nums_list():
    assert moving_average([], 3) == []

def test_window_size_of_one():
    assert moving_average([1, 2, 3, 4], 1) == [1, 2, 3, 4]

def test_window_size_equal_to_nums_length():
    assert moving_average([1, 2, 3, 4], 4) == [2.5]

def test_mixed_integer_and_float_values_in_nums():
    assert moving_average([1, 2.5, 3, 4.5], 2) == [1.75, 2.75, 3.75]

if __name__ == '__main__':
    import os
    with open('test_results.txt', 'w') as f:
        result = pytest.main(['-v', '--tb=short', '--disable-warnings'], plugins=[pytest.PytestTerminalReporter(verbosity=0)])
        for line in result.getvalue().splitlines():
            f.write(line + '\n')