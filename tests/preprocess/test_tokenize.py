from ingredient_parser.preprocess import tokenize


class TestTokenize:
    def test_simple_sentence(self):
        sentence = "1 tbsp mint sauce"
        assert tokenize(sentence) == ["1", "tbsp", "mint", "sauce"]

    def test_parens(self):
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
        sentence = '1" piece ginger, finely grated'
        assert tokenize(sentence) == [
            "1",
            '"',
            "piece",
            "ginger",
            ",",
            "finely",
            "grated",
        ]

    def test_colon_semicolon(self):
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
