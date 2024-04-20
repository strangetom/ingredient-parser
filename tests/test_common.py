import pytest

from ingredient_parser._common import (
    consume,
    is_float,
    is_range,
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

    def test_x(self):
        """
        Test string "1x" is correctly identified as not a range
        """
        assert not is_range("1x")
