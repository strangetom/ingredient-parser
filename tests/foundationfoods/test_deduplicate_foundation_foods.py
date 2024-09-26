from ingredient_parser.dataclasses import IngredientText
from ingredient_parser.en._foundationfoods import deduplicate_foundation_foods


class Teste_deduplicate_foundation_foods:
    def test_no_dupes(self):
        ff = [
            IngredientText("olive oil", 0.8),
            IngredientText("onion", 0.6),
        ]
        assert deduplicate_foundation_foods(ff) == ff

    def test_dupes(self):
        ff = [
            IngredientText("olive oil", 0.8),
            IngredientText("olive oil", 0.6),
        ]
        assert deduplicate_foundation_foods(ff) == [IngredientText("olive oil", 0.7)]
