#!/usr/bin/env python3

import gzip
import json
from pathlib import Path

import pycrfsuite


def export_crfsuite_to_json(model: pycrfsuite.Tagger, path: Path) -> None:
    """Export crfsuite model to gzipped json file.

    The exported json file contains the following fields:

    * attributes : dict[str, int]
      Name of each feature (key) and their index (value).
    * labels : dict[str int]
      Name of each label (key) and their index (value).
    * state_features :  dict[str, float]
      The weights for each feature for each label.
      The keys are the feature name and label joined with |.
      For example: bias:|QTY, where "bias:" is the feature name and "QTY" is the label.
    * transitions
      The weights for each label to label transition.
      The keys are the previous label and current label joined with |.
      For example: QTY|UNIT, where the previous label is "QTY" and the current label is
      "UNIT".

    Parameters
    ----------
    model : pycrfsuite.Tagger
        Trained model to export.
    path : Path
        Path to export model to.
    """
    info = model.info()
    j = {
        "attributes": {k: int(v) for k, v in info.attributes.items()},
        "labels": {k: int(v) for k, v in info.labels.items()},
        "state_features": {
            k[0] + "|" + k[1]: v for k, v in info.state_features.items()
        },
        "transitions": {k[0] + "|" + k[1]: v for k, v in info.transitions.items()},
    }

    with gzip.open(path.with_suffix(".json.gz"), "wt", encoding="utf-8") as f:
        json.dump(j, f)


def quantize(
    state_features: dict[str, float], transitions: dict[str, float], nbits: int
) -> tuple[dict[str, int], dict[str, int]]:
    """Quantize weights to nbit signed integer using linear scaling.

    Because the model weights are only used additively during inference, and we only
    consider the relative magnitudes of the weights, there is no need for keep the
    scaling factor because it would just be a multiplier of all of the weights.

    Parameters
    ----------
    state_features : dict[str, float]
        Dict of state features and their weight.
    transitions : dict[str, float]
        Dict of label transitions and their weight.
    nbits : int
        Number of bits for integer scaling.

    Returns
    -------
    tuple[dict[str, int], dict[str, int]]
        Quantized state_features and transitions dicts.
    """
    max_weight = max(max(state_features.values()), max(transitions.values()))
    scale = (2 ** (nbits - 1) - 1) / max_weight

    quantized_state_features = {}
    for feature, weight in state_features.items():
        quantized_weight = round(weight * scale)
        if quantized_weight != 0:
            quantized_state_features[feature] = quantized_weight

    quantized_transitions = {}
    for feature, weight in transitions.items():
        quantized_weight = round(weight * scale)
        if quantized_weight != 0:
            quantized_transitions[feature] = quantized_weight

    return quantized_state_features, quantized_transitions
