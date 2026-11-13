#!/usr/bin/env python3

import csv
import json
import sqlite3
from pathlib import Path

import spacy
import tqdm

from ingredient_parser._common import INTERMEDIATE_FRACTION_PATTERN, is_float
from ingredient_parser.en import PreProcessor
from ingredient_parser.en._tokenize import (
    FULL_STOP_TOKENISER,
    PUNCTUATION_TOKENISER,
    TRAILING_FULL_STOP,
    WHITESPACE_TOKENISER,
)
from ingredient_parser.en._utils import to_frac

sqlite3.register_adapter(list, json.dumps)


CSVS = [
    "bbc/bbc-ingredients-snapshot-2017.csv",
    "cookstr/cookstr-ingredients-snapshot-2017.csv",
    "nytimes/nyt-ingredients-snapshot-2015.csv",
    "allrecipes/allrecipes-ingredients-snapshot-2017.csv",
    "tastecooking/tastecooking-ingredients-snapshot-2024.csv",
    "manual/manual-ingredients.csv",
    "bonappetit/ba-ingredients.csv",
]

Token = tuple[str, bool]


def combine_and_or(tokens: list[Token]) -> list[Token]:
    """Combine ["and", "/", "or"] into a single token.
 
    This function retains the case of the original tokens. The combined token takes
    the followed-by-space flag of the final "or" token.
 
    Parameters
    ----------
    tokens : list[tuple[str, bool]]
        List of (token, followed_by_space) pairs.
 
    Returns
    -------
    list[tuple[str, bool]]
        Input tokens with any instances of and/or combined into a single token.
 
    Examples
    --------
    >>> combine_and_or([("beef", True), ("and", False), ("/", False), ("or", True), \
("chicken", False)])
    [('beef', True), ('and/or', True), ('chicken', False)]
 
    >>> combine_and_or([("1-2", True), ("bananas", False), (":", True), ("as", False)])
    [('1-2', True), ('bananas', False), (':', True), ('as', False)]
    """
    combined = []
    n = len(tokens)
    i = 0
    while i < n:
        if (
            tokens[i][0].lower() == "and"
            and i + 2 < n
            and tokens[i + 1][0] == "/"
            and tokens[i + 2][0].lower() == "or"
        ):
            combined.append((tokens[i][0] + "/" + tokens[i + 2][0], tokens[i + 2][1]))
            i += 3
        else:
            combined.append(tokens[i])
            i += 1

    return combined


def combine_no_number(tokens: list[Token]) -> list[Token]:
    """Combine "No." followed by a number into a single token.
 
    This function retains the case of the original tokens. The combined token takes
    the followed-by-space flag of the number token.
 
    Parameters
    ----------
    tokens : list[Token]
        List of (token, followed_by_space) pairs.
 
    Returns
    -------
    list[Token]
        Input tokens with any instances of No. followed by number combined into a single
        token.
 
    Examples
    --------
    >>> combine_no_number([("teaspoon", True), ("No.", True), ("1", True), \
("curing", False)])
    [('teaspoon', True), ('No. 1', True), ('curing', False)]
    """
    combined = []
    n = len(tokens)
    i = 0
    while i < n:
        if tokens[i][0].lower() == "no." and i + 1 < n and is_float(tokens[i + 1][0]):
            combined.append((tokens[i][0] + " " + tokens[i + 1][0], tokens[i + 1][1]))
            i += 2
        else:
            combined.append(tokens[i])
            i += 1

    return combined


def split_full_stops(tokens: list[Token]) -> list[Token]:
    """Split full stop from the end of a token.

    The full stop is not split from the end of a token if it preceded by a full stop
    then a word character, for example "U.S." does not have the trailing full stop
    split.

    When a token is split, the pieces before the last one are flagged as not followed by
    space (they were directly adjacent in the original text), and the last piece keeps
    the original token's flag.

    Parameters
    ----------
    tokens : list[Token]
        List of (token, followed_by_space) pairs.

    Returns
    -------
    list[Token]
        Input token with trailing full stops split from tokens.

    Examples
    --------
    >>> split_full_stops([("garnish.", False)])
    [('garnish', False), ('.', False)]

    >>> split_full_stops([("garnish.", True), ("now", False)])
    [('garnish', False), ('.', True), ('now', False)]

    >>> split_full_stops([("U.S.", True), ("beef", False)])
    [('U.S.', True), ('beef', False)]
    """
    split: list[Token] = []
    for text, space in tokens:
        if text.endswith("."):
            parts = [t for t in FULL_STOP_TOKENISER.split(text) if t]
            split.extend((t, False) for t in parts[:-1])
            split.append((parts[-1], space))
        else:
            split.append((text, space))

    return split


def tokenize(sentence: str) -> list[Token]:
    """Tokenise an ingredient sentence.
 
    The sentence is split on white space characters into a list of tokens.
    If any of these tokens contains of the punctuation marks captured by
    PUNCTUATION_TOKENISER, these are then split and isolated as a separate token.
 
    Each token is returned together with a boolean flag that is True if the token is
    immediately followed by a white space character in the original sentence, and
    False otherwise. A token at the very end of the sentence is only flagged True if
    the sentence has trailing white space.
 
    Empty tokens are never returned.

    NOTE
    This is a customised version of the tokenizer in ingredient_parser that returns
    tokens as a tuple of (str, bool), where the bool indicates if the token is followed
    by white space.
    This is required to define a custom tokenizer for use in a spaCy pipeline.
 
    Parameters
    ----------
    sentence : str
        Ingredient sentence to tokenize.
 
    Returns
    -------
    list[Token]
        List of (token, followed_by_space) pairs from sentence.
 
    Examples
    --------
    >>> tokenize("2 cups (500 ml) milk")
    [('2', True), ('cups', True), ('(', False), ('500', True), ('ml', False), \
(')', True), ('milk', False)]
 
    >>> tokenize("1-2 mashed bananas: as ripe as possible")
    [('1-2', True), ('mashed', True), ('bananas', False), (':', True), ('as', True), \
('ripe', True), ('as', True), ('possible', False)]
 
    >>> tokenize("1.5 kg bananas, mashed")
    [('1.5', True), ('kg', True), ('bananas', False), (',', True), ('mashed', False)]
 
    >>> tokenize("Freshly grated Parmesan cheese, for garnish.")
    [('Freshly', True), ('grated', True), ('Parmesan', True), ('cheese', False), \
(',', True), ('for', True), ('garnish', False), ('.', False)]
 
    >>> tokenize("2 onions, finely chopped*")
    [('2', True), ('onions', False), (',', True), ('finely', True), \
('chopped', False), ('*', False)]
 
    >>> tokenize("2 cups beef and/or chicken stock")
    [('2', True), ('cups', True), ('beef', True), ('and/or', True), \
('chicken', True), ('stock', False)]
    """
    # Split on white space, using finditer so we know where each white space delimited
    # token ends in the original sentence. Punctuation is then split out of each of
    # these tokens. Pieces of a token that were split apart were directly adjacent in
    # the sentence, so are not followed by a space; only the last piece takes the
    # flag for the original token, which is followed by white space unless it is at
    # the very end of the sentence (\S+ is greedy, so anything after it is white space).
    n = len(sentence)
    tokens: list[Token] = []
    for match in WHITESPACE_TOKENISER.finditer(sentence):
        pieces = [p for p in PUNCTUATION_TOKENISER.split(match.group()) if p]
        tokens.extend((p, False) for p in pieces[:-1])
        tokens.append((pieces[-1], match.end() < n))

    if "/" in sentence:
        # Recombine "and/or" into a single token.
        tokens = combine_and_or(tokens)

    if "no." in sentence.lower():
        # Recombine "No. 1" and similar into a single token.
        tokens = combine_no_number(tokens)

    if TRAILING_FULL_STOP.search(" ".join(text for text, _ in tokens)):
        # Second pass to separate full stops from end of tokens, but only if we have
        # detected a full stop followed by a space or the end of the string.
        # Otherwise there's no need to do anything. The check is run on the tokens
        # joined by spaces, rather than on the sentence, so that a full stop followed
        # by punctuation, e.g. "(garnish.)", is detected as it was originally.
        tokens = split_full_stops(tokens)

    return tokens


class CustomTokenizer:
    def __init__(self, vocab):
        self.vocab = vocab

    def __call__(self, sentence: str) -> spacy.tokens.Doc:
        """Custom tokenizer that calls the modified version of ingredient_parser's
        tokenize function.

        The sentences passed to this tokenizer have been normalized by
        ingredient_parser.en.PreProcessor, which means that fractions have been
        converted to the intermediate format. spaCy cannot be expected to understand
        fractions represented in that way, so all intermediate form fractions are
        converted to decimals. This makes them unambiguously numbers to spaCy whilst
        still being treated as a single token.

        Parameters
        ----------
        sentence : str
            Sentence to tokenize.

        Returns
        -------
        spacy.tokens.Doc
            Tokenized sentences as a spaCy.tokens.Doc object.
        """
        tokens, spaces = zip(*tokenize(sentence))

        fixed_tokens = []
        for tok in tokens:
            if INTERMEDIATE_FRACTION_PATTERN.fullmatch(tok):
                # If the token is of the form 1#1$2 or #1$2, convert to decimal.
                fixed_tokens.append(str(float(to_frac(tok))))
            else:
                fixed_tokens.append(tok)

        return spacy.tokens.Doc(self.vocab, words=fixed_tokens, spaces=list(spaces))


if __name__ == "__main__":
    base_path = Path("train/data")
    # Load recipe ingredient sentences from CSV files and normalise them.
    # Keep the original sentence and the normalized sentence:
    #     The original sentence is stored in the database.
    #     The normalised sentence is parsed.
    # We only keep unique sentences.
    unique_sentences = set()
    for file in CSVS:
        with open(base_path / file) as f:
            print(f"Reading data from '{file}'.")
            reader = csv.reader(f)
            for row in reader:
                if row[0]:
                    sentence = PreProcessor(row[0]).sentence
                    unique_sentences.add((row[0], sentence))

    # Split into lists of original and normalized sentences.
    original, normalized = zip(*unique_sentences)
    original = list(original)
    normalized = list(normalized)

    spacy.require_gpu()
    # Use spaCy's transformer model for highest accuracy.
    nlp = spacy.load("en_core_web_trf")
    # Add doc_cleaner to pipeline to keep GPU memory usage under control.
    nlp.add_pipe("doc_cleaner")
    # Replace default tokenizer with customised one.
    nlp.tokenizer = CustomTokenizer(nlp.vocab)

    training_data = []
    # Process in batches for speed.
    # Batch size chosen to comfortably fit in 4GB GPU memory.
    text_stream = nlp.pipe(normalized, batch_size=128)
    print("Parsing sentences...")
    for i, (original_sentence, doc) in tqdm.tqdm(
        enumerate(zip(original, text_stream)), total=len(unique_sentences)
    ):
        tokens = [t.text for t in doc]
        tags = [t.tag_ for t in doc]
        deps = [t.dep_ for t in doc]

        training_data.append((i, original_sentence, tokens, tags, deps))

    # Store in database.
    print("Storing parsed sentences in 'train/data/pos_deps.sqlite3'.")
    with sqlite3.connect(
        base_path / "pos_deps.sqlite3", detect_types=sqlite3.PARSE_DECLTYPES
    ) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM en")
        c.executemany(
            "INSERT INTO en (id, sentence, tokens, tags, deps) VALUES (?, ?, ?, ?, ?)",
            training_data,
        )
    conn.close()
