import type { AlgoVariant } from "../../../domain";

interface AlgoDescriptiveOptionItem {
	value: AlgoVariant;
	description: string;
}

const algorithms: AlgoDescriptiveOptionItem[] = [
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

export default algorithms;
