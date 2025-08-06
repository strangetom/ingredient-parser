from unittest.mock import patch

import pytest

from ingredient_parser._common import (
    consume,
    group_consecutive_idx,
    is_float,
    is_range,
    show_model_card,
)


class Test_consume:
    def test_conume(self):
        """
        Test iterator advances by specified amount
        """
        it = iter(range(0, 10))
        assert next(it) == 0
        consume(it, 2)
        assert next(it) == 3

    def test_consume_all(self):
        """
        Test iterator is consumed completely
        """
        it = iter(range(0, 10))
        assert next(it) == 0
        consume(it, None)
        with pytest.raises(StopIteration):
            next(it)


class Test_is_float:
    def test_int(self):
        """
        Test string "1" is correctly identified as convertable to float
        """
        assert is_float("1")

    def test_float(self):
        """
        Test string "2.5" is correctly identified as convertable to float
        """
        assert is_float("2.5")

    def test_range(self):
        """
        Test string "1-2" is correctly identified as not convertable to float
        """
        assert not is_float("1-2")

    def test_x(self):
        """
        Test string "1x" is correctly identified as not convertable to float
        """
        assert not is_float("1x")


class Test_is_range:
    def test_int(self):
        """
        Test string "1" is correctly identified as not a range
        """
        assert not is_range("1")

    def test_float(self):
        """
        Test string "2.5" is correctly identified as not a range
        """
        assert not is_range("2.5")

    def test_range(self):
        """
        Test string "1-2" is correctly identified as not a range
        """
        assert is_range("1-2")

    def test_range_extra(self):
        """
        Test string "1-2 dozen" is correctly identified as not a range
        """
        assert not is_range("1-2 dozen")

    def test_x(self):
        """
        Test string "1x" is correctly identified as not a range
        """
        assert not is_range("1x")


class Test_group_consecutive_indices:
    def test_single_group(self):
        """
        Return single group
        """
        input_indices = [0, 1, 2, 3, 4]
        groups = group_consecutive_idx(input_indices)
        assert [list(g) for g in groups] == [input_indices]

    def test_multiple_groups(self):
        """
        Return groups of consecutive indices
        """
        input_indices = [0, 1, 2, 4, 5, 6, 8, 9]
        groups = group_consecutive_idx(input_indices)
        assert [list(g) for g in groups] == [[0, 1, 2], [4, 5, 6], [8, 9]]


class Test_show_model_card:
    @patch("os.startfile", create=True)
    @patch("subprocess.call")
    def test_model_card_found(self, mock_startfile, mock_subprocess_call):
        """Test model card found at path derived from selected language.

        The calls to os.startfile and subprocess.call are mocked to prevent the model
        card from actually opening.
        """
        try:
            show_model_card("en")
        except FileNotFoundError:
            pytest.fail("Model card not found.")
