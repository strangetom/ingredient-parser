import pytest

from ingredient_parser.en import PostProcessor


@pytest.fixture
def p():
    """Define an empty PostProcessor object to use for testing the PostProcessor
    class methods.
    """
    return PostProcessor(".", [], {})


class Test_group_name_labels:
    def test_single_name(self, p):
        """
        Input sequence is returned the same.
        """
        input_labels = ["B_NAME_TOK", "I_NAME_TOK", "I_NAME_TOK"]
        expected = [[(0, "B_NAME_TOK"), (1, "I_NAME_TOK"), (2, "I_NAME_TOK")]]
        assert p._group_name_labels(input_labels) == expected

    def test_single_name_with_punc(self, p):
        """
        Input sequence is returned the same, including punctuation.
        """
        input_labels = ["B_NAME_TOK", "I_NAME_TOK", "PUNC", "I_NAME_TOK", "I_NAME_TOK"]
        expected = [
            [
                (0, "B_NAME_TOK"),
                (1, "I_NAME_TOK"),
                (2, "PUNC"),
                (3, "I_NAME_TOK"),
                (4, "I_NAME_TOK"),
            ]
        ]
        assert p._group_name_labels(input_labels) == expected

    def test_multiple_names(self, p):
        """
        Input sequence is split into two groups, on the second B_NAME_TOK
        """
        input_labels = ["B_NAME_TOK", "I_NAME_TOK", "PUNC", "B_NAME_TOK", "I_NAME_TOK"]
        expected = [
            [(0, "B_NAME_TOK"), (1, "I_NAME_TOK"), (2, "PUNC")],
            [(3, "B_NAME_TOK"), (4, "I_NAME_TOK")],
        ]
        assert p._group_name_labels(input_labels) == expected

    def test_name_var(self, p):
        """
        NAME_VARs are returned as separate groups, because they are not consecutive.
        """
        input_labels = ["NAME_VAR", "NAME_SEP", "NAME_VAR", "B_NAME_TOK", "I_NAME_TOK"]
        expected = [
            [(0, "NAME_VAR")],
            [(2, "NAME_VAR")],
            [(3, "B_NAME_TOK"), (4, "I_NAME_TOK")],
        ]
        assert p._group_name_labels(input_labels) == expected

    def test_consecutuve_name_vars(self, p):
        """
        First two NAME_VARs are grouped together as they are consecutive.
        """
        input_labels = [
            "NAME_VAR",
            "NAME_VAR",
            "NAME_SEP",
            "NAME_VAR",
            "B_NAME_TOK",
            "I_NAME_TOK",
        ]
        expected = [
            [(0, "NAME_VAR"), (1, "NAME_VAR")],
            [(3, "NAME_VAR")],
            [(4, "B_NAME_TOK"), (5, "I_NAME_TOK")],
        ]
        assert p._group_name_labels(input_labels) == expected

    def test_non_consecutuve_name_vars(self, p):
        """
        First two NAME_VARs are grouped together as they are consecutive.
        """
        input_labels = [
            "NAME_VAR",
            "PUNC",
            "NAME_VAR",
            "NAME_SEP",
            "NAME_VAR",
            "B_NAME_TOK",
            "I_NAME_TOK",
        ]
        expected = [
            [(0, "NAME_VAR"), (1, "PUNC")],
            [(2, "NAME_VAR")],
            [(4, "NAME_VAR")],
            [(5, "B_NAME_TOK"), (6, "I_NAME_TOK")],
        ]
        assert p._group_name_labels(input_labels) == expected

    def test_name_mod_and_name_var(self, p):
        """
        NAME_MOD and NAME_VARs are in groups of their own.
        """
        input_labels = [
            "NAME_MOD",
            "NAME_VAR",
            "NAME_SEP",
            "NAME_VAR",
            "B_NAME_TOK",
            "I_NAME_TOK",
        ]
        expected = [
            [(0, "NAME_MOD")],
            [(1, "NAME_VAR")],
            [(3, "NAME_VAR")],
            [(4, "B_NAME_TOK"), (5, "I_NAME_TOK")],
        ]
        assert p._group_name_labels(input_labels) == expected

    def test_multiple_name_mod_no_name_sep(self, p):
        """
        All NAME_MODs and intervening PUNCs are grouped into one group.
        """
        input_labels = [
            "NAME_MOD",
            "PUNC",
            "NAME_MOD",
            "PUNC",
            "NAME_MOD",
            "B_NAME_TOK",
            "NAME_SEP",
            "B_NAME_TOK",
        ]
        expected = [
            [
                (0, "NAME_MOD"),
                (1, "PUNC"),
                (2, "NAME_MOD"),
                (3, "PUNC"),
                (4, "NAME_MOD"),
            ],
            [(5, "B_NAME_TOK")],
            [(7, "B_NAME_TOK")],
        ]
        assert p._group_name_labels(input_labels) == expected

    def test_multiple_name_mod_with_name_sep(self, p):
        """
        NAME_MODs and intervening PUNCs either side of the NAME_SEP are grouped.
        """
        input_labels = [
            "NAME_MOD",
            "PUNC",
            "NAME_MOD",
            "NAME_SEP",
            "NAME_MOD",
            "B_NAME_TOK",
            "NAME_SEP",
            "B_NAME_TOK",
        ]
        expected = [
            [(0, "NAME_MOD"), (1, "PUNC"), (2, "NAME_MOD")],
            [(4, "NAME_MOD")],
            [(5, "B_NAME_TOK")],
            [(7, "B_NAME_TOK")],
        ]
        assert p._group_name_labels(input_labels) == expected

    def test_multiple_name_mod_name_var_name_tok(self, p):
        """
        NAME_MODs and intervening PUNCs either side of the NAME_SEP are grouped.
        """
        input_labels = [
            "NAME_MOD",
            "NAME_MOD",
            "NAME_SEP",
            "NAME_MOD",
            "NAME_VAR",
            "PUNC",
            "NAME_VAR",
            "NAME_VAR",
            "NAME_SEP",
            "NAME_VAR",
            "B_NAME_TOK",
            "I_NAME_TOK",
            "NAME_SEP",
            "B_NAME_TOK",
        ]
        expected = [
            [(0, "NAME_MOD"), (1, "NAME_MOD")],
            [(3, "NAME_MOD")],
            [(4, "NAME_VAR"), (5, "PUNC")],
            [(6, "NAME_VAR"), (7, "NAME_VAR")],
            [(9, "NAME_VAR")],
            [(10, "B_NAME_TOK"), (11, "I_NAME_TOK")],
            [(13, "B_NAME_TOK")],
        ]
        assert p._group_name_labels(input_labels) == expected

    def test_name_tok_before_name_mod(self, p):
        """
        First B_NAME_TOK is grouped on it's own, followed by 2 groups for subsequence
        NAME_MOD groups.
        """
        input_labels = [
            "B_NAME_TOK",
            "PUNC",
            "NAME_MOD",
            "PUNC",
            "NAME_SEP",
            "NAME_MOD",
            "B_NAME_TOK",
            "I_NAME_TOK",
            "NAME_SEP",
            "B_NAME_TOK",
        ]
        expected = [
            [(0, "B_NAME_TOK"), (1, "PUNC")],
            [(2, "NAME_MOD"), (3, "PUNC")],
            [(5, "NAME_MOD")],
            [(6, "B_NAME_TOK"), (7, "I_NAME_TOK")],
            [(9, "B_NAME_TOK")],
        ]
        assert p._group_name_labels(input_labels) == expected
