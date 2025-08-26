import type { Amount, Confidence, FoundationFood, Token } from "./classesTypes";

export interface InputTabParser {
	sentence: string;
	discard_isolated_stop_words: boolean;
	expect_name_in_output: boolean;
	string_units: boolean;
	imperial_units: boolean;
	foundation_foods: boolean;
	separate_names: boolean;
}

export interface InputHistoryTabPaser extends Input {
	timestamp: string;
}

export interface ParsedTabParser {
	amounts: Amount[];
	foundation_foods: FoundationFood[];
	comment: Confidence;
	name: Confidence[];
	preparation: Confidence;
	purpose: Confidence;
	size: Confidence;
	tokens: Token[];
}

export interface Input {
	sentence: string;
	discard_isolated_stop_words: boolean;
	expect_name_in_output: boolean;
	string_units: boolean;
	imperial_units: boolean;
	foundation_foods: boolean;
}
