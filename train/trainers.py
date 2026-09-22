#!/usr/bin/env python3

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pycrfsuite

logger = logging.getLogger(__name__)


class IngredientParserTrainer(pycrfsuite.Trainer):  # type: ignore
    """Custom modification of the pycrfsuite.Trainer class to provide more useful
    logging.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._iterations = 0
        self._start_time = 0
        self.stopping_reason = None

    def on_start(self, log):
        """Callback called on start of training.

        Parameters
        ----------
        log : str
            Log line emitted from crfsuite.
        """
        self._start_time = time.time()
        logger.info("Training started at %s", time.strftime("%H:%M:%S"))

    def on_featgen_progress(self, log, percent):
        """Callback called on during feature generation.

        Parameters
        ----------
        log : str
            Log line emitted from crfsuite.
        percent : int
            Percentage of feature generation complete.
        """
        ...

    def on_featgen_end(self, log):
        """Callback called on end of feature generation.

        Parameters
        ----------
        log : str
            Log line emitted from crfsuite.
        """
        ...

    def on_prepared(self, log):
        """Callback called on training preparation completed.

        Parameters
        ----------
        log : str
            Log line emitted from crfsuite.
        """
        logger.info("Training model with training data.")

    def on_optimization_end(self, log):
        """Callback called on end of optimisation.

        Parameters
        ----------
        log : str
            Log line emitted from crfsuite.
        """
        log_lines = [line for line in log.splitlines() if line]
        if len(log_lines) > 1:
            self.stopping_reason = log_lines[0]

    def on_iteration(self, log: str, info: dict[str, Any]):
        """Callback called on every training iteration.

        Parameters
        ----------
        log : str
            Log line emitted from crfsuite.
        info : dict[str, Any]
            Log line converted to dict with the following keys:
                num (iteration number)
                loss
                feature_norm
                error_norm
                active_features
                linesearch_trials
                linesearch_step
                time
        """
        self._iterations += 1

    def on_end(self, log):
        """Callback called on end of training.

        Parameters
        ----------
        log : str
            Log line emitted from crfsuite.
        """
        elapsed_time = timedelta(seconds=int(time.time() - self._start_time))
        logger.info("Model trained in %s.", elapsed_time)
        logger.info("Stopped after %d iterations.", self._iterations)

    def write_model_config(
        self, model_file: Path, extra_parameters: dict[str, int | float | bool | None]
    ) -> Path:
        """Write configuration JSON file detail model parameters.

        Parameters
        ----------
        model_file : Path
            Path to model file to generate config for.
        extra_parameters : dict[str, None | int | float | bool]
            Dict of extra model hyperparameters to include in config.


        Returns
        -------
        Path
            Config file path.
        """
        if model_file.suffix == ".gz" and model_file.stem.endswith(".json"):
            # Strip suffix (to remove '.gz').
            config_file = model_file.with_suffix("")
        else:
            config_file = model_file.with_suffix(".json")

        config = self.get_params()
        config["datetime"] = datetime.now().isoformat()
        config["stopping_reason"] = self.stopping_reason

        config.update(extra_parameters)

        with open(model_file, "rb", buffering=0) as f:
            config["sha256"] = hashlib.file_digest(f, "sha256").hexdigest()

        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)

        return config_file
