#!/usr/bin/env python3

import json
import sqlite3
import sys
from collections import defaultdict
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

from tabulate import tabulate

# Ensure the local ingredient_parser package can be found
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ingredient_parser.en import PreProcessor
from ingredient_parser.inference import PROHIBITED_TRANSITIONS

sqlite3.register_converter("json", json.loads)

DATABASE = "train/data/training.sqlite3"


@dataclass
class DBRow:
    id: int
    source: str
    sentence: str
    tokens: list[str]
    labels: list[str]
    sentence_split: list[int]
    fdc_mapping: int


@dataclass
class CalculatedTokenError:
    id: int
    sentence: str
    calculated_tokens: list[str]
    database_tokens: list[str]


@dataclass
class DuplicateSentenceError:
    sentence: str
    ids: list[int]
    label_sequences: list[tuple[str, ...]]


@dataclass
class LabelError:
    id: int
    error: str


@dataclass
class ValidationResults:
    calculated_token: list[CalculatedTokenError]
    token_count: list[CalculatedTokenError]
    duplicate_sentence: list[DuplicateSentenceError]
    prohibited_transition: list[LabelError]
    i_name_tok: list[LabelError]
    name_var: list[LabelError]
    name_mod: list[LabelError]


class TrainingDataValidator:
    def __init__(self):
        """Load training data from database."""
        with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            data = c.execute("SELECT * FROM en")

        self.training_data = [DBRow(**d) for d in data]
        conn.close()

        self.validation_results = ValidationResults(
            calculated_token=[],
            token_count=[],
            duplicate_sentence=[],
            prohibited_transition=[],
            i_name_tok=[],
            name_var=[],
            name_mod=[],
        )

    def validate(self):
        """Validate database entries and print any errors."""
        self.validate_sentence_consistency(self.training_data)

        for row in self.training_data:
            self.validate_token_consistency(row)
            self.validate_label_consistency(row)

        # Display results...
        if len(self.validation_results.token_count) > 0:
            n = len(self.validation_results.token_count)
            print(
                (
                    f"{n} sentences where number of database tokens "
                    "do not match PreProcessor output:"
                )
            )
            print(
                ",".join(
                    [str(error.id) for error in self.validation_results.token_count]
                )
            )

        if len(self.validation_results.calculated_token) > 0:
            n = len(self.validation_results.calculated_token)
            print(
                f"{n} sentences where database tokens do not match PreProcessor output:"
            )
            print(
                ",".join(
                    [
                        str(error.id)
                        for error in self.validation_results.calculated_token
                    ]
                )
            )

            for error in self.validation_results.calculated_token:
                table = [
                    ["PreProcessor", error.calculated_tokens],
                    ["Database", error.database_tokens],
                ]
                print(
                    tabulate(
                        table,
                        headers=[f"ID: {error.id}", error.sentence],
                        tablefmt="fancy_grid",
                        maxcolwidths=[None, None],
                        stralign="left",
                        numalign="right",
                    )
                )

        if len(self.validation_results.duplicate_sentence) > 0:
            n = len(self.validation_results.duplicate_sentence)
            print(f"{n} duplicate sentence with different label sequences:")
            table = []
            for error in self.validation_results.duplicate_sentence:
                table.append([error.sentence, ",".join(map(str, error.ids))])

            print(
                tabulate(
                    table,
                    headers=["Sentence", "IDs"],
                    tablefmt="fancy_grid",
                    maxcolwidths=[None, None],
                    stralign="left",
                    numalign="right",
                )
            )

        if (
            self.validation_results.prohibited_transition
            or self.validation_results.i_name_tok
            or self.validation_results.name_var
            or self.validation_results.name_mod
        ):
            print("Label sequence errors:")
            label_error_table = [
                [
                    "Prohibited transitions",
                    len(self.validation_results.prohibited_transition),
                    ",".join(
                        {
                            str(error.id)
                            for error in self.validation_results.prohibited_transition
                        }
                    ),
                ],
                [
                    "I_NAME_TOK",
                    len(self.validation_results.i_name_tok),
                    ",".join(
                        {str(error.id) for error in self.validation_results.i_name_tok}
                    ),
                ],
                [
                    "NAME_VAR",
                    len(self.validation_results.name_var),
                    ",".join(
                        {str(error.id) for error in self.validation_results.name_var}
                    ),
                ],
                [
                    "NAME_MOD",
                    len(self.validation_results.name_mod),
                    ",".join(
                        {str(error.id) for error in self.validation_results.name_mod}
                    ),
                ],
            ]
            print(
                tabulate(
                    label_error_table,
                    headers=["Error", "Count", "IDs"],
                    tablefmt="fancy_grid",
                    maxcolwidths=[None, None],
                    stralign="left",
                    numalign="right",
                )
            )

    def validate_sentence_consistency(self, rows: list[DBRow]) -> None:
        """Validate duplicate sentences have the same label sequence.

        Parameters
        ----------
        rows : list[DBRow]
            List of database rows.
        """
        sentence_labels = defaultdict(set)
        sentence_ids = defaultdict(set)
        for row in rows:
            sentence_labels[row.sentence].add(tuple(row.labels))
            sentence_ids[row.sentence].add(row.id)

        for sentence, label_sequences in sentence_labels.items():
            if len(label_sequences) > 1:
                self.validation_results.duplicate_sentence.append(
                    DuplicateSentenceError(
                        sentence=sentence,
                        ids=list(sentence_ids[sentence]),
                        label_sequences=list(label_sequences),
                    )
                )

    def validate_token_consistency(self, row: DBRow) -> None:
        """Validate consistency between tokens stored in database and those calculated
        by PreProcessor

        Parameters
        ----------
        calculated_tokens : list[str]
            Tokens calculated by PreProcessor.
        row : DBRow
            Database row.
        """
        p = PreProcessor(row.sentence)
        calculated_tokens = [t.text for t in p.tokenized_sentence]

        if len(calculated_tokens) != len(row.tokens):
            self.validation_results.token_count.append(
                CalculatedTokenError(
                    id=row.id,
                    sentence=row.sentence,
                    calculated_tokens=calculated_tokens,
                    database_tokens=row.tokens,
                )
            )
        elif calculated_tokens != row.tokens:
            self.validation_results.calculated_token.append(
                CalculatedTokenError(
                    id=row.id,
                    sentence=row.sentence,
                    calculated_tokens=calculated_tokens,
                    database_tokens=row.tokens,
                )
            )

    def validate_label_consistency(self, row: DBRow) -> None:
        """Validate label sequence consistency with labelling scheme.

        Check for the following:
        * No prohibited transitions are present.
        * No instances of I_NAME_TOK occurring before B_NAME_TOK since start of sequence
          of last NAME_SEP.
        * No instances of a single NAME_VAR.
        * No instances of a NAME_MOD without at least 2 B_NAME_TOK or 2 NAME_VAR.

        Parameters
        ----------
        row : DBRow
            Database row.
        """
        if not self._validate_I_NAME_TOK(row):
            self.validation_results.i_name_tok.append(
                LabelError(
                    id=row.id, error="I_NAME_TOK does not occur after B_NAME_TOK."
                )
            )

        if error := self._validate_NAME_VAR(row):
            self.validation_results.name_var.append(LabelError(id=row.id, error=error))

        if not self._validate_NAME_MOD(row):
            self.validation_results.name_mod.append(
                LabelError(
                    id=row.id,
                    error="NAME_MOD is not followed by 2+ NAME_VAR or B_NAME_TOK.",
                )
            )

        if error := self._validate_prohibited_transitions(row):
            self.validation_results.prohibited_transition.append(
                LabelError(id=row.id, error=error)
            )

    def _validate_I_NAME_TOK(self, row: DBRow) -> bool:
        """Validate that I_NAME_TOK always appears after a B_NAME_TOK.

        I_NAME_TOK does not have to be adjacent to B_NAME_TOK.

        If the sentence contains NAME_SEP, check there is a B_NAME_TOK after the
        NAME_SEP before any I_NAME_TOK.

        Parameters
        ----------
        row : DBRow
            Database row.

        Returns
        -------
        bool
            True if valid, else False.
        """
        if "I_NAME_TOK" not in row.labels:
            return True

        for i, label in enumerate(row.labels):
            if label != "I_NAME_TOK":
                continue

            if "NAME_SEP" in row.labels[:i]:
                # If NAME_SEP prior to current I_NAME_TOK, check there is a B_NAME_TOK
                # after NAME_SEP and before current label.
                name_sep_idx = max(
                    i for i, v in enumerate(row.labels[:i]) if v == "NAME_SEP"
                )
                if "B_NAME_TOK" not in row.labels[name_sep_idx:i]:
                    return False
            else:
                if "B_NAME_TOK" not in row.labels[:i]:
                    return False

        return True

    def _validate_NAME_VAR(self, row: DBRow) -> str | None:
        """Validate if the sentence contains NAME_VAR, there is more than one.

        If there is more than one, check there is at least one B_NAME_TOK in the
        sentence too.

        Parameters
        ----------
        row : DBRow
            Database row.

        Returns
        -------
        str | None
            Return None if sequence is valid with respect to NAME_VAR labels.
            If the sequence is not valid, return an error message.
        """
        if "NAME_VAR" not in row.labels:
            return None

        # Check if there is only one NAME_VAR.
        name_var_count = sum(1 for label in row.labels if label == "NAME_VAR")
        if name_var_count == 1:
            return "Single NAME_VAR label."

        # Check if there is not B_NAME_TOK, given that there is at least two NAME_VAR.
        b_name_tok_count = sum(1 for label in row.labels if label == "B_NAME_TOK")
        if b_name_tok_count == 0:
            return "NAME_VAR not followed by B_NAME_TOK."

        # Check that at least one B_NAME_TOK occurs after the last NAME_VAR.
        last_name_var_idx = max(i for i, v in enumerate(row.labels) if v == "NAME_VAR")
        last_b_name_tok_idx = max(
            i for i, v in enumerate(row.labels) if v == "B_NAME_TOK"
        )
        if last_name_var_idx > last_b_name_tok_idx:
            return "NAME_VAR is not followed by B_NAME_TOK."

        return None

    def _validate_NAME_MOD(self, row: DBRow) -> bool:
        """Validate if the sentence contains NAME_MOD, there are at least 2 B_NAME_TOK
        or at least 2 NAME_VAR after the NAME_MOD.

        Parameters
        ----------
        row : DBRow
            Database row.

        Returns
        -------
        bool
            True if valid, else False.
        """
        if "NAME_MOD" not in row.labels:
            return True

        name_mod_idx = max(i for i, v in enumerate(row.labels) if v == "NAME_MOD")

        name_var_count = sum(
            1 for label in row.labels[name_mod_idx:] if label == "NAME_VAR"
        )
        b_name_tok_count = sum(
            1 for label in row.labels[name_mod_idx:] if label == "B_NAME_TOK"
        )
        if not (
            b_name_tok_count >= 2 or (name_var_count >= 2 and b_name_tok_count >= 1)
        ):
            return False

        return True

    def _validate_prohibited_transitions(self, row: DBRow) -> str | None:
        """Validate than none of the label transitions are defined in the
        PROHIBITED_TRANSITIONS constant.

        !IMPORTANT!
        A label transition that is found in the training data that is also in the
        PROHIBITED_TRANSITIONS does not always mean the sentence is labelled
        incorrectly.
        It could be that the PROHIBITED_TRANSITIONS is incorrect and needs updating.

        Parameters
        ----------
        row : DBRow
            Database row.

        Returns
        -------
        bool
            True if valid, else False.
        """
        for l1, l2 in pairwise(row.labels):
            if l2 in PROHIBITED_TRANSITIONS.get(l1, set()):
                return f"Transition from {l1} → {l2} is in PROHIBITED_TRANSITIONS."

        return None


if __name__ == "__main__":
    validator = TrainingDataValidator()
    validator.validate()
