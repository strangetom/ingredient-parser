import type { AlgoVariant } from "../types";

interface CollectionAlgoDescriptiveOption {
	value: AlgoVariant;
	description: string;
}

export const collectionsAlgorithms: CollectionAlgoDescriptiveOption[] = [
	{
		value: "lbfgs",
		description: "Gradient descent using the L-BFGS method",
	},
	{
		value: "ap",
		description: " Averaged Perceptron",
	},
	{
		value: "l2sgd",
		description: "Stochastic Gradient Descent with L2 regularization term",
	},
	{
		value: "pa",
		description: "Passive Aggressive",
	},
	{
		value: "arow",
		description: "Adaptive Regularization of Weight Vector",
	},
];
