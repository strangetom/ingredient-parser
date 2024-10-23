from ingredient_parser.en._utils import tokenize


class TestTokenize:
    def test_simple_sentence(self):
        """
        Test simple sentence is tokenised correctly
        """
        sentence = "1 tbsp mint sauce"
        assert tokenize(sentence) == ["1", "tbsp", "mint", "sauce"]

    def test_parens(self):
        """
        Test parentheses are correctly isolated as tokens
        """
        sentence = "14 ounce (400 g) can chickpeas"
        assert tokenize(sentence) == [
            "14",
            "ounce",
            "(",
            "400",
            "g",
            ")",
            "can",
            "chickpeas",
        ]

    def test_square_brackets(self):
        """
        Test square brackets are correctly isolated as tokens
        """
        sentence = "14 ounce [400 g] can chickpeas"
        assert tokenize(sentence) == [
            "14",
            "ounce",
            "[",
            "400",
            "g",
            "]",
            "can",
            "chickpeas",
        ]

    def test_curly_braces(self):
        """
        Test curly braces are correctly isolated as tokens
        """
        sentence = "14 ounce {400 g} can chickpeas"
        assert tokenize(sentence) == [
            "14",
            "ounce",
            "{",
            "400",
            "g",
            "}",
            "can",
            "chickpeas",
        ]

    def test_comma_quote(self):
        """
        Test quote and comma are correctly isolated as tokens
        """
        sentence = '1" piece ginger, finely grated'
        assert tokenize(sentence) == [
            '1"',
            "piece",
            "ginger",
            ",",
            "finely",
            "grated",
        ]

    def test_colon_semicolon(self):
        """
        Test colon and semicolon are correctly isolated as tokens
        """
        sentence = "Egg wash: 2 egg yolks; whisked"
        assert tokenize(sentence) == [
            "Egg",
            "wash",
            ":",
            "2",
            "egg",
            "yolks",
            ";",
            "whisked",
        ]

    def test_degree_symbol(self):
        """
        Test degree symbol is correctly kept within tokens
        """
        sentence = "0.25 cup warm water (105°F)"
        assert tokenize(sentence) == [
            "0.25",
            "cup",
            "warm",
            "water",
            "(",
            "105°F",
            ")",
        ]

    def test_full_stop(self):
        """
        Test full stop at end of sentence is separated from prior word.
        """
        sentence = "Freshly grated Parmesan cheese, for garnish."
        assert tokenize(sentence) == [
            "Freshly",
            "grated",
            "Parmesan",
            "cheese",
            ",",
            "for",
            "garnish",
            ".",
        ]

    def test_full_stop_acronym(self):
        """
        Test full stop at end of acronym is not separated.
        """
        sentence = "Sprigs of herbs (e.g., rosemary, thyme, or oregano)"
        assert tokenize(sentence) == [
            "Sprigs",
            "of",
            "herbs",
            "(",
            "e.g.",
            ",",
            "rosemary",
            ",",
            "thyme",
            ",",
            "or",
            "oregano",
            ")",
        ]

    def test_asteriks(self):
        """
        Test asterisk at end of word is separated.
        """
        sentence = "2 onions, finely chopped*"
        assert tokenize(sentence) == ["2", "onions", ",", "finely", "chopped", "*"]

    def test_fake_fraction(self):
        """
        Test fake fraction is no separated.
        """
        sentence = "#1$2 cups milk"
        assert tokenize(sentence) == ["#1$2", "cups", "milk"]
