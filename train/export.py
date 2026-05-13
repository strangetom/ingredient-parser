#!/usr/bin/env python3

import gzip
import io
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pycrfsuite


@dataclass
class CRFModelParameters:
    attributes: dict[str, int]
    labels: dict[str, int]
    state_features: dict[str, float]
    transitions: dict[str, float]


def export_crfsuite_to_json(
    model: pycrfsuite.Tagger,
    path: Path,
    quantize_bits: int | None,
    min_abs_weight: float | None,
) -> None:
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
    quantize_bits : int | None
        Number of bits to quantize the model to, or None to disable quantization.
    min_abs_weight : float | None
        Weights with an absolute value less than this are pruned, or None to disable
        weight pruning.
    """
    info = model.info()
    params = CRFModelParameters(
        attributes={k: int(v) for k, v in info.attributes.items()},
        labels={k: int(v) for k, v in info.labels.items()},
        state_features={k[0] + "|" + k[1]: v for k, v in info.state_features.items()},
        transitions={k[0] + "|" + k[1]: v for k, v in info.transitions.items()},
    )

    if min_abs_weight is not None:
        params = prune_weights(params, min_abs_weight)

    if quantize_bits is not None:
        params = quantize(params, quantize_bits)

    # We use gzip.GzipFile and io.TextIOWrapper so that we can set mtime=0 for the gzip.
    # This removes the timestamp from the output file meaning it is always identical
    # for the same set of model weights.
    with gzip.GzipFile(path, mode="wb", mtime=0) as gz:
        with io.TextIOWrapper(gz, encoding="utf-8") as f:
            json.dump(asdict(params), f)


def quantize(params: CRFModelParameters, nbits: int) -> CRFModelParameters:
    """Quantize weights to nbit signed integer using linear scaling.

    Because the model weights are only used additively during inference, and we only
    consider the relative magnitudes of the weights, there is no need for keep the
    scaling factor because it would just be a multiplier of all of the weights.

    Parameters
    ----------
    params : CRFModelParameters
        CRF model parameters
    nbits : int
        Number of bits for integer scaling.

    Returns
    -------
    CRFModelParameters
        Model parameters with quantized state_features and transitions.
    """
    max_weight = max(
        max(params.state_features.values()), max(params.transitions.values())
    )
    scale = (2 ** (nbits - 1) - 1) / max_weight

    quantized_state_features = {}
    for feature, weight in params.state_features.items():
        quantized_weight = round(weight * scale)
        if quantized_weight != 0:
            quantized_state_features[feature] = quantized_weight

    quantized_transitions = {}
    for feature, weight in params.transitions.items():
        quantized_weight = round(weight * scale)
        if quantized_weight != 0:
            quantized_transitions[feature] = quantized_weight

    params.state_features = quantized_state_features
    params.transitions = quantized_transitions
    return params


def prune_weights(
    params: CRFModelParameters, min_abs_weight: float
) -> CRFModelParameters:
    """Prune weights by removing weights less than 5% of the maximum weight.

    Parameters
    ----------
    params : CRFModelParameters
        CRF model parameters
    min_abs_weight : float
        Minimum absolute weight to keep.

    Returns
    -------
    CRFModelParameters
        Model parameters with pruned state_features and transitions.
    """
    params.state_features = {
        feature: weight
        for feature, weight in params.state_features.items()
        if abs(weight) >= min_abs_weight
    }
    params.transitions = {
        feature: weight
        for feature, weight in params.transitions.items()
        if abs(weight) >= min_abs_weight
    }
    return params
