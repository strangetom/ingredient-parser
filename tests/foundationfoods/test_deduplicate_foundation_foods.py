from ingredient_parser.dataclasses import FoundationFood
from ingredient_parser.en._foundationfoods import deduplicate_foundation_foods


class Teste_deduplicate_foundation_foods:
    def test_no_dupes(self):
        ff = [
            FoundationFood("olive oil", 0.8),
            FoundationFood("onion", 0.6),
        ]
        assert deduplicate_foundation_foods(ff) == ff

    def test_dupes(self):
        ff = [
            FoundationFood("olive oil", 0.8),
            FoundationFood("olive oil", 0.6),
        ]
        assert deduplicate_foundation_foods(ff) == [FoundationFood("olive oil", 0.7)]
