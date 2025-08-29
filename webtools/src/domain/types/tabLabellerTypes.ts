import type { LabellerCategory, Token } from "./classesTypes";

export type ParsedSentence = {
	id?: number | string;
	labels: string[];
	sentence: string;
	source: string;
	tokens: Token[];
};

export interface ParsedSentenceEditable extends ParsedSentence {
	edited?: boolean;
	removed?: boolean;
	plain?: boolean;
}

export interface ParsedTabLabller {
	data: ParsedSentence[];
	offset: number;
	total: number;
}

export type InputSettings = {
	caseSensitive: boolean;
	wholeWord: boolean;
	sources: string[];
	labels: LabellerCategory[];
};

export interface InputTabLabeller {
	sentence: string;
	settings: InputSettings;
}
