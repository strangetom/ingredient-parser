import type { AlgoVariant, AlgoVariantStoreNamespace } from "../../../domain";

export const algorithmsVariantToNamespace = {
	global: "algosGlobalParams",
	lbfgs: "algosLBFGSParams",
	ap: "algosAPParams",
	l2sgd: "algosL2SGDParams",
	pa: "algosPAParams",
	arow: "algosAROWParams",
} as Record<AlgoVariant, AlgoVariantStoreNamespace>;

export const algorithmsNamespaceToVariant = {
	algosGlobalParams: "global",
	algosLBFGSParams: "lbfgs",
	algosAPParams: "ap",
	algosL2SGDParams: "l2sgd",
	algosPAParams: "pa",
	algosAROWParams: "arow",
} as Record<AlgoVariantStoreNamespace, AlgoVariant>;
