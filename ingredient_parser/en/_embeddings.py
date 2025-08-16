#!/usr/bin/env python3

import gzip
from importlib.resources import as_file, files
from typing import Any

import numpy as np


class GloVeModel:
    """Class to interact with GloVe embeddings.

    Attributes
    ----------
    binarized_vectors : dict[str, list[str]]
        Dict of word: binarized_vector pairs.
    vec_file : str
        Path to GloVe embeddings file.
    vectors : dict[str, np.ndarray]
        Dict of word: vector pairs.
    """

    def __init__(self, vec_file: str):
        """Initialise.

        Parameters
        ----------
        vec_file : str
            Path to GloVe embeddings file.
        """
        self.vec_file = vec_file
        self._load_vectors_from_file(vec_file)
        self._binarize_vectors()

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
        (i.e. number of vectors) and the dimensions of the vectors.

        All remaining rows contain the token followed by the numeric elements of the
        vector, separated by a space

        Parameters
        ----------
        vec_file : str
            Path to GloVe embeddings file.
        """
        self.vectors = {}
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
                    self.vectors[token] = vector

    def _binarize_vectors(self):
        """Binarize vectors by converting continuous values into discrete values [1].

        For each word vector, calculate the average value of the positive elements and
        the negative elements. Replace each element of each word vector according to:
        if value < negative_average:
            "VNEG"
        elif value > positive_average
            "VPOS"
        else
            "V0"

        The resulting word vectors are stored in the binarized_vectors attribute.

        References
        ----------
        .. [1] J. Guo, W. Che, H. Wang, and T. Liu, ‘Revisiting Embedding Features for
           Simple Semi-supervised Learning’, in Proceedings of the 2014 Conference on
           EmpiricalMethods in Natural Language Processing (EMNLP), Doha, Qatar:
           Association for Computational Linguistics, 2014, pp. 110–120.
           doi: 10.3115/v1/D14-1012.
        """
        self.binarized_vectors = {}
        for word, vec in self.vectors.items():
            positive_avg = np.mean(vec[vec > 0])
            negative_avg = np.mean(vec[vec < 0])

            binarised_vec = []
            for value in vec:
                if value < negative_avg:
                    binarised_vec.append("VNEG")
                elif value > positive_avg:
                    binarised_vec.append("VPOS")
                else:
                    binarised_vec.append("V0")

            self.binarized_vectors[word] = binarised_vec
