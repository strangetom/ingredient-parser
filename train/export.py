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
    state_features: dict[str, float | int]
    transitions: dict[str, float | int]
    quantization_scale: float
    quantization_zero_offset: int


def export_crfsuite_to_json(
    model: pycrfsuite.Tagger,  # type: ignore
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
      The keys are the feature name and label joined with \u001f (ASCII unit separator).
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
        state_features={"\u001f".join(k): v for k, v in info.state_features.items()},
        transitions={"\u001f".join(k): v for k, v in info.transitions.items()},
        quantization_scale=1.0,
        quantization_zero_offset=0,
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
    max_weight = 0
    for w in params.state_features.values():
        max_weight = max(max_weight, abs(w))
    for w in params.transitions.values():
        max_weight = max(max_weight, abs(w))
    scale = (2 ** (nbits - 1) - 1) / max_weight

    # Keep track of features with a non-zero weight after quantization.
    nonzero_state_features = set()

    quantized_state_features = {}
    for feature, weight in params.state_features.items():
        quantized_weight = round(weight * scale)
        if quantized_weight != 0:
            quantized_state_features[feature] = quantized_weight

            # Get name of feature and add to nonzero_state_features.
            attr = feature.split("\u001f", 1)[0]
            nonzero_state_features.add(attr)

    quantized_transitions = {}
    for feature, weight in params.transitions.items():
        quantized_weight = round(weight * scale)
        if quantized_weight != 0:
            quantized_transitions[feature] = quantized_weight

    # Iterate over attributes and only keep features in the nonzero_features set.
    idx = 0
    updated_attributes = {}
    for attribute in params.attributes.keys():
        if attribute in nonzero_state_features:
            updated_attributes[attribute] = idx
            idx += 1

    params.state_features = quantized_state_features
    params.transitions = quantized_transitions
    params.attributes = updated_attributes
    params.quantization_scale = scale
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
