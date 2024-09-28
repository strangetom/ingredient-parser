from ingredient_parser.dataclasses import FoudationFood
from ingredient_parser.en._foundationfoods import deduplicate_foundation_foods


class Teste_deduplicate_foundation_foods:
    def test_no_dupes(self):
        ff = [
            FoudationFood("olive oil", 0.8),
            FoudationFood("onion", 0.6),
        ]
        assert deduplicate_foundation_foods(ff) == ff

    def test_dupes(self):
        ff = [
            FoudationFood("olive oil", 0.8),
            FoudationFood("olive oil", 0.6),
        ]
        assert deduplicate_foundation_foods(ff) == [FoudationFood("olive oil", 0.7)]
