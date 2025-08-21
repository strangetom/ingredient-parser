/*
 *  Types here are cross-referenced with command line argparse types found on
 *  github.com/strangetom/ingredient-parser/blob/master/train.py
 *
 *  Ingredient parser library supports single, multiple, gridsearch, and featuresearch tasks on argparse
 *  Webtools only supports single or multiple (i.e. "basic") and gridsearch (i.e. "gridsearch")
 *
 */

export type TrainerMode = "tuner" | "trainer";

export type InputTrainerTask = "training" | "gridsearch";

export type AlgoVariant = "lbfgs" | "ap" | "l2sgd" | "pa" | "arow" | "global";

export type AlgoVariantStoreNamespace =
	| "algosGlobalParams"
	| "algosLBFGSParams"
	| "algosAPParams"
	| "algosL2SGDParams"
	| "algosPAParams"
	| "algosAROWParams";

export type InputTrainerShared = {
	split: number;
	seed: number;
	sources: string[];
	debugLevel: number;
	combineNameLabels: boolean;
};

export type InputTrainer = {
	html: boolean;
	runs: number;
	runsCategory: string;
	processes: number;
	detailed: boolean;
	confusion: boolean;
} & InputTrainerShared;

export type InputTrainerGridSearch = {
	processes: number;
	algos: AlgoVariant[];
	algosGlobalParams: string;
	algosLBFGSParams: string;
	algosAPParams: string;
	algosL2SGDParams: string;
	algosPAParams: string;
	algosAROWParams: string;
} & InputTrainerShared;
