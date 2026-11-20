import json
import sqlite3
from collections import defaultdict
from contextlib import closing
from dataclasses import dataclass
from itertools import chain, zip_longest

import tqdm
from tabulate import tabulate

from ingredient_parser.dataclasses import IngredientText, LabelledToken
from ingredient_parser.en import PostProcessor, PreProcessor
from ingredient_parser.en.foundationfoods._ff_utils import load_fdc_ingredients

sqlite3.register_converter("json", json.loads)
sqlite3.register_converter("list", json.loads)
sqlite3.register_adapter(list, json.dumps)

DATABASE = "train/data/training.sqlite3"


@dataclass
class DBRow:
    id: int
    sentence: str
    labels: list[str]
    fdc_mapping: int


@dataclass
class Sentence:
    uid: int
    sentence: str
    name_mapping: list[tuple[str | None, int | None]]


class TrainingDataValidator:
    def __init__(self):
        """Load training data from database."""
        with closing(
            sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        ) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            data = c.execute("SELECT id, sentence, labels, fdc_mapping FROM en")
            self.training_data = [DBRow(**d) for d in data]

        self.parse_sentences(self.training_data)

        # Create a dict mapping FDC ID to FDC description
        self.fdc_id_to_description = {
            fdc.fdc_id: fdc.description for fdc in load_fdc_ingredients()
        }

    def parse_sentences(self, sentences: list[DBRow]):
        """Parse sentences (using true labels) to create a dict that maps an ingredient
        name to an FDC ID.

        Whilst parsing the sentences, keep track of the sentences that have names
        without mappings to FDC IDs (in the missing_mapping list) and sentences where
        the database contains mappings inconsistent with the number of names (in the
        inconsistent_mapping list) due to having a different number of FDC IDs than
        names.

        Parameters
        ----------
        sentences : list[DBRow]
            List of items in the database.
        """
        # fdc_name_map is a dict of dicts.
        # The outer key is an ingredient name.
        # The inner key is the FDC ID mapped to the outer ingredient name.
        # The inner value is a list of sentences that contain that mapping.
        # In theory, each name should only have one FDC ID mapped to it and therefore
        # the inner dict should only have one key. In reality, there are mistakes.
        self.fdc_name_map = defaultdict(lambda: defaultdict(list))

        # List of sentences with inconsistent mappings (more FDC IDs than names).
        self.inconsistent_mapping = []
        # List of sentences with names without a mapped FDC ID.
        self.missing_mapping = []

        for item in tqdm.tqdm(sentences):
            # Parse sentence using true labels instead of calling parse_ingredient.
            processed_sentence = PreProcessor(item.sentence)
            labelled_tokens = [
                LabelledToken(
                    index=token.index,
                    text=token.text,
                    pos_tag=token.pos_tag,
                    label=label,
                    score=1.0,
                    plural=token.index in processed_sentence.singularised_indices,
                )
                for token, label in zip(
                    processed_sentence.tokenized_sentence, item.labels
                )
            ]
            p = PostProcessor(item.sentence, labelled_tokens, custom_units={}).parsed

            # Create mapping, a list of (name, FDC ID) pairs.
            if len(p.name) < len(item.fdc_mapping):
                # More FDC IDs listed in database than names.
                mapping = [
                    (name.text, fdc_id)
                    for name, fdc_id in zip_longest(
                        p.name, item.fdc_mapping, fillvalue=IngredientText(None, 0, 0)
                    )
                ]
            else:
                mapping = [
                    (name.text, fdc_id)
                    for name, fdc_id in zip_longest(
                        p.name, item.fdc_mapping, fillvalue=None
                    )
                ]

            sent = Sentence(uid=item.id, sentence=item.sentence, name_mapping=mapping)

            if any(name is None for name, _ in mapping):
                # If any names are None it means there are more FDC IDs than names.
                self.inconsistent_mapping.append(sent)
                continue

            if any(fdc is None for _, fdc in mapping):
                # If any FDC IDs are None, there is a missing mapping.
                self.missing_mapping.append(sent)

            # Add name to fdc_name_map.
            for name, fdc_id in mapping:
                if fdc_id is not None:
                    self.fdc_name_map[name][fdc_id].append(sent)

    def validate(self):
        """Validate FDC ID mappings.

        * Output sentences with more FDC IDs than names.
        * Output names with more than one FDC ID mapping.
        """
        print(
            (
                f"{len(self.inconsistent_mapping)} sentences with inconsistent "
                "number of names and FDC mappings:"
            )
        )
        print(",".join(str(sent.uid) for sent in self.inconsistent_mapping))
        print()

        names_with_multiple_fdc_id_mappings = [
            name for name, fdc_ids in self.fdc_name_map.items() if len(fdc_ids) > 1
        ]
        print(
            (
                f"{len(names_with_multiple_fdc_id_mappings)} ingredient names "
                "mapped to multiple FDC IDs:"
            )
        )
        # Generate table.
        # 1st column is the name.
        # 2nd column is the FDC mappings, separated by |. Each mapping has the form
        # "fdc_id (description) [sentence count]"
        # 3rd column is the list of sentence IDs that contain the name.
        table = [
            [
                name,
                " | ".join(
                    (
                        (
                            f"{fdc_id} ({self.fdc_id_to_description[fdc_id]}) "
                            f"[{len(self.fdc_name_map[name][fdc_id])}]"
                        )
                        for fdc_id in self.fdc_name_map[name]
                    )
                ),
                ",".join(
                    (
                        str(s.uid)
                        for s in chain.from_iterable(self.fdc_name_map[name].values())
                    )
                ),
            ]
            for name in names_with_multiple_fdc_id_mappings
        ]
        print(
            tabulate(
                sorted(table, key=lambda row: len(row[2])),
                headers=["Ingredient name", "FDC IDs", "Sentence IDs"],
                tablefmt="fancy_grid",
                maxcolwidths=[None, 50, None],
                stralign="left",
                numalign="right",
            )
        )
        print()

    def suggest_mappings(self):
        """Suggest mapping for names without an FDC ID"""

        table = []
        sentence_uids = []
        for sentence in self.missing_mapping:
            new_suggestion = False
            updated_mapping = []
            for name, fdc_id in sentence.name_mapping:
                if name is None:
                    # No name, so can't suggest anything.
                    continue
                if fdc_id is not None:
                    # Mapping exists, so skip.
                    updated_mapping.append((name, fdc_id, False))
                    continue

                guess = self.fdc_name_map.get(name)
                if guess is None or len(guess) != 1:
                    # If the fdc_name_map contains multiple FDC IDs for the name, then
                    # we can't suggest anything.
                    continue

                guess = next(iter(guess))
                new_suggestion = True
                updated_mapping.append((name, guess, True))

            if new_suggestion:
                sentence_uids.append(sentence.uid)
                for name, fdc_id, is_new in updated_mapping:
                    if is_new:
                        # 1st column: sentence uid
                        # 2nd column: name:
                        # 3rd column: suggest fdc_id (description)
                        table.append(
                            [
                                sentence.uid,
                                name,
                                f"{fdc_id} ({self.fdc_id_to_description[fdc_id]})",
                            ]
                        )

        print(f"{len(sentence_uids)} sentences could have FDC IDs mapped to names.")
        print(
            tabulate(
                sorted(table, key=lambda row: row[1]),
                headers=["Sentence ID", "Name", "Suggested FDC ID"],
                tablefmt="fancy_grid",
                maxcolwidths=[None, 80, 80],
                stralign="left",
                numalign="right",
            )
        )
        print(",".join(str(uid) for uid in sentence_uids))
        print()


if __name__ == "__main__":
    validator = TrainingDataValidator()
    validator.validate()
    validator.suggest_mappings()
