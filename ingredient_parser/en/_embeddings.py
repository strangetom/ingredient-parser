#!/usr/bin/env python3

import array
import gzip
from importlib.resources import as_file, files
from typing import Any

import numpy as np


class GloVeModel:
    """Class to interact with GloVe embeddings.

    Attributes
    ----------
    vec_file : str
        Path to GloVe embeddings file.
    vectors : np.ndarray
        Embedding vectors, one per row.
    index : dict[str, int]
        Dict mapping word to row index in vectors array.
    """

    def __init__(self, vec_file: str):
        """Initialise.

        Parameters
        ----------
        vec_file : str
            Path to GloVe embeddings file.
        """
        self.vec_file = vec_file
        self.index, self.vectors = self._load_vectors_from_file(vec_file)

    def __repr__(self) -> str:
        return f"GloVeModel(vec_file={self.vec_file})"

    def __str__(self) -> str:
        return f"GloVeModel(vocab_size={self.vocab_size}, dimensions={self.dimension})"

    def __len__(self) -> int:
        return self.vocab_size

    def __contains__(self, token: str) -> bool:
        return token in self.index

    def __getitem__(self, token: str) -> np.ndarray:
        return self.vectors[self.index[token]]

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
        row = self.index.get(token)
        if row is None:
            return default

        return self.vectors[row]

    def _load_vectors_from_file(self, file: str) -> tuple[dict[str, int], np.ndarray]:
        """Load vectors from gzipped .txt file in word2vec format.

        The first line of the file contains the header which is the vocabulary size
        (i.e. number of vectors) and the dimensions of the vectors.

        All remaining rows contain the token followed by the numeric elements of the
        vector, separated by a space.

        Parameters
        ----------
        file : str
            Path to GloVe embeddings file.

        Returns
        -------
        tuple[dict[str, int], np.ndarray]
            Dict mapping token to row of vectors array.
            Vectors array of embedding vectors.
        """
        index = {}
        # Create an array to store the embedding vectors in during loading.
        # All vectors are loaded into this single buffer, rather than creating one
        # buffer per embedding token.
        buf = array.array("f")
        with as_file(files(__package__) / file) as p:
            with gzip.open(p, "rt") as f:
                # Read first line as header
                header = f.readline().rstrip()
                self.vocab_size, self.dimension = map(int, header.split())

                # Read remaining rows and load vectors
                for row_number, line in enumerate(f):
                    parts = line.rstrip().split()
                    index[parts[0]] = row_number
                    buf.extend([float(v) for v in parts[1:]])

        # Convert buffer array into NumPy array.
        return index, np.frombuffer(buf, dtype=np.float32).reshape(-1, self.dimension)

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

        # Average of the positive and negative elements of each vector (row of matrix).
        # These are calculated one row at a time, on only the selected elements, so the
        # float32 results are exactly those of np.mean(vec[vec > 0]), etc.
        n_tokens = len(self.vectors)
        positive_avg = np.empty(n_tokens, dtype=self.vectors.dtype)
        negative_avg = np.empty(n_tokens, dtype=self.vectors.dtype)
        for row, vec in enumerate(self.vectors):
            positive_avg[row] = np.mean(vec[vec > 0])
            negative_avg[row] = np.mean(vec[vec < 0])

        binarized = np.full(self.vectors.shape, "V0", dtype="<U4")
        binarized[self.vectors > positive_avg[:, np.newaxis]] = "VPOS"
        binarized[self.vectors < negative_avg[:, np.newaxis]] = "VNEG"

        rows = binarized.tolist()
        self.binarized_vectors = {word: rows[row] for word, row in self.index.items()}
