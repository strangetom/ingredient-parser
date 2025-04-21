#!/usr/bin/env python3

import gzip
from importlib.resources import as_file, files
from typing import Any

import numpy as np


class GloVeModel:
    def __init__(self, vec_file: str):
        self.vec_file = vec_file
        self._load_vectors_from_file(vec_file)

    def __repr__(self) -> str:
        return f"GloVeModel(vec_file={self.vec_file})"

    def __str__(self) -> str:
        return f"GloVeModel(vocab_size={self.vocab_size}, dimensions={self.dimension})"

    def __len__(self) -> int:
        return self.vocab_size

    def __contains__(self, token: str) -> bool:
        return token in self.vectors

    def __getitem__(self, token: str) -> np.ndarray:
        return self.vectors[token]

    def get(self, token: str, default: Any) -> Any:
        """If token in vector keys, return vector, otherwise return default.

        Parameters
        ----------
        token : str
            Token to return vector for.
        default : Any
            Default value if token not in vector keys.

        Returns
        -------
        Any
            Vector, or default value.
        """
        if token in self.vectors:
            return self.vectors[token]
        else:
            return default

    def _load_vectors_from_file(self, vec_file: str) -> None:
        """Load vectors from gzipped txt file in word2vec format.

        The first line of the file contains the header which is the vocabulary size
        (i.e. number of vectors) and the dimenisions of the vectors.

        All remaining rows contain the token followed by the numeric elements of the
        vector, separated by a space

        Parameters
        ----------
        vec_file : str
            File to load vectors from.
        """
        vectors = {}
        with as_file(files(__package__) / vec_file) as p:
            with gzip.open(p, "rt") as f:
                # Read first line as header
                header = f.readline().rstrip()
                self.vocab_size, self.dimension = map(int, header.split())

                # Read remaining lines and load vectors
                for line in f:
                    parts = line.rstrip().split()
                    token = parts[0]
                    vector = np.array([float(v) for v in parts[1:]], dtype=np.float32)
                    vectors[token] = vector

        self.vectors = vectors
