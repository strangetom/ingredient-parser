from ingredient_parser.en import PostProcessor


class TestPostProcessor_match_pattern:
    def test_long_pattern_match(self):
        """
        Test that correct start and stop indices are returned for long pattern
        """
        pattern = ["QTY", "QTY", "UNIT", "QTY", "UNIT", "QTY", "UNIT", "UNIT"]

        labels = [
            "QTY",
            "UNIT",
            "QTY",
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
            "UNIT",
        ]
        p = PostProcessor("", [], [], [], [])

        assert p._match_pattern(labels, pattern, ignore_other_labels=True) == [
            [2, 3, 4, 5, 6, 7, 8, 9]
        ]

    def test_medium_pattern_match(self):
        """
        Test that correct start and stop indices are returned for medium pattern
        """
        pattern = ["QTY", "QTY", "UNIT", "QTY", "UNIT", "UNIT"]

        labels = [
            "QTY",
            "QTY",
            "UNIT",
            "QTY",
            "UNIT",
            "UNIT",
            "UNIT",
        ]
        p = PostProcessor("", [], [], [], [])

        assert p._match_pattern(labels, pattern, ignore_other_labels=True) == [
            [0, 1, 2, 3, 4, 5]
        ]

    def test_short_pattern_match(self):
        """
        Test that correct start and stop indices are returned for long pattern
        """
        pattern = ["QTY", "QTY", "UNIT", "UNIT"]

        labels = [
            "QTY",
            "UNIT",
            "QTY",
            "QTY",
            "UNIT",
            "UNIT",
            "QTY",
            "UNIT",
            "UNIT",
        ]
        p = PostProcessor("", [], [], [], [])

        assert p._match_pattern(labels, pattern, ignore_other_labels=True) == [
            [2, 3, 4, 5]
        ]

    def test_impossible_match(self):
        """
        Test that empty list is returned when match is impossible beacause pattern
        is longer than list of labels
        """
        pattern = ["QTY", "QTY", "UNIT", "QTY", "UNIT", "UNIT"]

        labels = [
            "QTY",
            "QTY",
            "UNIT",
            "UNIT",
        ]
        p = PostProcessor("", [], [], [], [])

        assert p._match_pattern(labels, pattern, ignore_other_labels=True) == []

    def test_multiple_matches(self):
        """
        Test that multiple non-overlapping matches are returned
        """
        pattern = ["QTY", "QTY", "UNIT", "UNIT"]

        labels = [
            "QTY",
            "QTY",
            "UNIT",
            "UNIT",
            "QTY",
            "QTY",
            "QTY",
            "UNIT",
            "UNIT",
        ]
        p = PostProcessor("", [], [], [], [])

        assert p._match_pattern(labels, pattern, ignore_other_labels=True) == [
            [0, 1, 2, 3],
            [5, 6, 7, 8],
        ]

    def test_interrupted_pattern_without_ignore(self):
        """
        Test that an interrupted pattern is not matched if ignore_other_labels set False
        """
        pattern = ["QTY", "QTY", "UNIT", "UNIT"]

        labels = [
            "QTY",
            "QTY",
            "COMMENT",
            "UNIT",
            "UNIT",
        ]
        p = PostProcessor("", [], [], [], [])

        assert p._match_pattern(labels, pattern, ignore_other_labels=False) == []

    def test_interrupted_pattern_with_ignore(self):
        """
        Test that an interrupted pattern is matched if ignore_other_labels set True
        """
        pattern = ["QTY", "QTY", "UNIT", "UNIT"]

        labels = [
            "QTY",
            "QTY",
            "COMMENT",
            "UNIT",
            "UNIT",
        ]
        p = PostProcessor("", [], [], [], [])

        assert p._match_pattern(labels, pattern, ignore_other_labels=True) == [
            [0, 1, 3, 4]
        ]
