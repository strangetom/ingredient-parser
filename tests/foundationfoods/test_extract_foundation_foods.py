from ingredient_parser.en import PreProcessor
from ingredient_parser.en._foundationfoods import extract_foundation_foods


class Test_extract_foundation_foods:
    def test_extract(self):
        p = PreProcessor("1 cup finely chopped red onion")
        tokens = [t.text for t in p.tokenized_sentence]
        features = p.sentence_features()
        labels = ["QTY", "UNIT", "PREP", "PREP", "NAME", "NAME"]

        ff = extract_foundation_foods(tokens, labels, features)
        assert len(ff) == 1
        assert ff[0].text == "red onion"

    def test_no_FF_token(self):
        p = PreProcessor("1 cup finely chopped")
        tokens = [t.text for t in p.tokenized_sentence]
        features = p.sentence_features()
        labels = ["QTY", "UNIT", "PREP", "PREP"]

        assert extract_foundation_foods(tokens, labels, features) == []
