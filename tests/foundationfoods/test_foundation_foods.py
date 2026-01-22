import pytest

from ingredient_parser import parse_ingredient

OVERRIDE_EXAMPLES = [
    ("1 egg", 748967),
    ("2 eggs", 748967),
    ("1 tbsp salt", 746775),
    ("4 cloves garlic, crushed", 1104647),
]

SIMPLE_EXAMPLES = [
    ("½ yellow bell pepper, chopped", 2258589),
    ("8 large strawberries, hulled and halved", 2346409),
    ("1 cup white wine", 2710689),
    ("1 lg yellow onion, chopped", 790646),
    ("3 red chili peppers, seeded and finely chopped", 170106),
    ("1/2 teaspoon ground ginger", 170926),
    ("2 large red onions, sliced", 790577),
    ("3 skinless, boneless chicken breasts, chopped into 2 cm cubes", 2646170),
    ("200 g canned chopped tomatoes", 2685581),
    ("4 tbsp tomato ketchup", 2709733),
    ("small handful fresh parsley, leaves picked and chopped", 170416),
]

BIAS_EXAMPLES = [
    ("2 red or green peppers", (2258588, 2258590)),
    ("2 cooked red or green peppers", (2709976, 2709977)),
]

MULTIPLE_EXAMPLES = [
    ("salt and black pepper", (170931, 746775)),
    ("24 fresh basil leaves or dried basil", (172232, 171317)),
    ("2 red or green peppers", (2258588, 2258590)),
    ("250 ml hot beef or chicken stock", (172883, 172884)),
]

NO_MATCH_EXAMPLES = ["twelve bonbons"]

NO_EMBEDDING_TOKENS = [
    ("1 waxgourd", 170069),  # not in embeddings, but has FDC match
    ("200 g lionfish", None),  # not in embeddings and no FDC match
]


class TestPostProcessor_match_foundation_foods:
    @pytest.mark.parametrize(("sentence", "fdc_id"), OVERRIDE_EXAMPLES)
    def test_match_foundation_foods_overrides(self, sentence, fdc_id):
        """
        Test that each example sentence returns the correct foundation food override.
        """
        p = parse_ingredient(sentence, foundation_foods=True)
        assert p.foundation_foods != []
        assert p.foundation_foods[0].fdc_id == fdc_id
        assert p.foundation_foods[0].confidence == 1

    @pytest.mark.parametrize(("sentence", "fdc_id"), SIMPLE_EXAMPLES)
    def test_match_foundation_foods_simple(self, sentence, fdc_id):
        """
        Test that each example sentence returns the correct foundation food.
        """
        p = parse_ingredient(sentence, foundation_foods=True)
        assert p.foundation_foods != []
        assert p.foundation_foods[0].fdc_id == fdc_id

    @pytest.mark.parametrize(("sentence", "fdc_id"), SIMPLE_EXAMPLES)
    def test_match_foundation_foods_simple_combined_names(self, sentence, fdc_id):
        """
        Test that each example sentence returns the correct foundation food.
        """
        p = parse_ingredient(sentence, separate_names=False, foundation_foods=True)
        assert p.foundation_foods != []
        assert p.foundation_foods[0].fdc_id == fdc_id

    @pytest.mark.parametrize(("sentence", "fdc_ids"), MULTIPLE_EXAMPLES)
    def test_match_foundation_foods_multiple(self, sentence, fdc_ids):
        """
        Test that each example sentence returns the correct foundation foods.
        """
        p = parse_ingredient(sentence, foundation_foods=True)
        assert len(p.foundation_foods) > 1
        for ff in p.foundation_foods:
            assert ff.fdc_id in fdc_ids

    @pytest.mark.parametrize(("sentence", "fdc_ids"), BIAS_EXAMPLES)
    def test_match_foundation_foods_bias(self, sentence, fdc_ids):
        """
        Test that each example sentence returns the correct foundation foods.
        """
        p = parse_ingredient(sentence, foundation_foods=True)
        assert len(p.foundation_foods) > 1
        for ff in p.foundation_foods:
            assert ff.fdc_id in fdc_ids

    @pytest.mark.parametrize("sentence", NO_MATCH_EXAMPLES)
    def test_match_foundation_foods_no_match(self, sentence):
        """
        Test that each example sentence returns no foundation food.
        """
        p = parse_ingredient(sentence, foundation_foods=True)
        assert p.foundation_foods == []

    @pytest.mark.parametrize(("sentence", "fdc_id"), NO_EMBEDDING_TOKENS)
    def test_match_foundation_foods_no_embeddings(self, sentence, fdc_id):
        """
        Test that each example sentence returns no foundation food.
        """
        p = parse_ingredient(sentence, foundation_foods=True)
        if fdc_id:
            assert p.foundation_foods != []
            assert p.foundation_foods[0].fdc_id == fdc_id
        else:
            assert p.foundation_foods == []
