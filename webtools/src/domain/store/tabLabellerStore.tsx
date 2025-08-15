// {{{EXTERNAL}}}

import type { UseListStateHandlers } from "@mantine/hooks";
import { notifications } from "@mantine/notifications";
import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import { constructEndpoint } from "../api";
// {{{INTERNAL}}}
import type {
	InputSettings,
	InputTabLabeller,
	LabellerCategory,
	ParsedSentence,
	ParsedSentenceEditable,
	ParsedTabLabller,
} from "../types";

type TabLabellerInputProvided =
	| {
			input?: InputTabLabeller;
			offsetPage?: number;
			shouldAddToHistory?: boolean;
	  }
	| undefined;

interface TabLabellerState {
	loading: boolean;
	editing: boolean;
	preuploading: boolean;
	uploading: boolean;
	error: boolean;
	success: boolean;
	activePage: number;
	setActivePage: (page: number) => void;
	editModeEnabled: boolean;
	setEditModeEnabled: (enabled: boolean) => void;
	input: InputTabLabeller;
	updateInput: (partial: Partial<InputTabLabeller>) => void;
	updateInputSettings: (partial: Partial<InputSettings>) => void;
	parsed: ParsedTabLabller | null;
	setParsed: (data: ParsedTabLabller | null) => void;
	parsedSentencesOriginal: ParsedSentenceEditable[];
	parsedSentences: ParsedSentenceEditable[];
	parsedSentencesHandler: Omit<
		UseListStateHandlers<ParsedSentenceEditable>,
		"setState"
	> & { set: (items: ParsedSentenceEditable[]) => void };
	getLabellerSearchApi: (opts?: TabLabellerInputProvided) => void;
	editLabellerItemsApi: () => Promise<boolean>;
	parseNewLabellerItemsForUploadApi: (
		value: string,
	) => Promise<ParsedSentenceEditable[] | null>;
	availablePublisherSources: string[];
	fetchingAvailablePublisherSources: boolean;
	fetchAvailableSourcesApi: () => Promise<string[]>;
}

export const defaultInputLabeller = {
	sentence: "",
	settings: {
		caseSensitive: false,
		wholeWord: false,
		sources: ["nyt", "cookstr", "allrecipes", "bbc", "tc", "saveur"],
		labels: [
			"COMMENT",
			"B_NAME_TOK",
			"I_NAME_TOK",
			"NAME_VAR",
			"NAME_MOD",
			"NAME_SEP",
			"PREP",
			"PUNC",
			"PURPOSE",
			"QTY",
			"SIZE",
			"UNIT",
			"OTHER",
		] as LabellerCategory[],
	},
};

export const useTabLabellerStore = create(
	subscribeWithSelector<TabLabellerState>((set, get) => ({
		loading: false,
		editing: false,
		preuploading: false,
		uploading: false,
		error: false,
		success: false,
		activePage: 0,
		setActivePage: (page: number) => set({ activePage: page }),
		editModeEnabled: false,
		setEditModeEnabled: (enabled: boolean) => set({ editModeEnabled: enabled }),
		input: defaultInputLabeller,
		updateInput: (partial: Partial<InputTabLabeller>) =>
			set(({ input }) => ({ input: { ...input, ...partial } })),
		updateInputSettings: (partial: Partial<InputSettings>) =>
			set(({ input }) => ({
				input: { ...input, settings: { ...input.settings, ...partial } },
			})),
		parsed: null,
		setParsed: (data: ParsedTabLabller | null) => set({ parsed: data }),
		parsedSentencesOriginal: [],
		parsedSentences: [],
		parsedSentencesHandler: {
			set: (items: ParsedSentenceEditable[]) => set({ parsedSentences: items }),
			append: (...items: ParsedSentenceEditable[]) =>
				set(({ parsedSentences }) => ({
					parsedSentences: [...parsedSentences, ...items],
				})),
			prepend: (...items: ParsedSentenceEditable[]) =>
				set(({ parsedSentences }) => ({
					parsedSentences: [...items, ...parsedSentences],
				})),
			insert: (index: number, ...items: ParsedSentenceEditable[]) =>
				set(({ parsedSentences }) => ({
					parsedSentences: [
						...parsedSentences.slice(0, index),
						...items,
						...parsedSentences.slice(index),
					],
				})),
			pop: () =>
				set(({ parsedSentences }) => {
					const cloned = [...parsedSentences];
					cloned.pop();
					return { parsedSentences: cloned };
				}),
			shift: () =>
				set(({ parsedSentences }) => {
					const cloned = [...parsedSentences];
					cloned.shift();
					return { parsedSentences: cloned };
				}),
			apply: (
				fn: (item: ParsedSentenceEditable, index?: number) => ParsedSentence,
			) =>
				set(({ parsedSentences }) => ({
					parsedSentences: parsedSentences.map((item, index) =>
						fn(item, index),
					),
				})),
			applyWhere: (
				condition: (item: ParsedSentenceEditable, index: number) => boolean,
				fn: (item: ParsedSentenceEditable, index?: number) => ParsedSentence,
			) =>
				set(({ parsedSentences }) => ({
					parsedSentences: parsedSentences.map((item, index) =>
						condition(item, index) ? fn(item, index) : item,
					),
				})),
			remove: (...indices: number[]) =>
				set(({ parsedSentences }) => ({
					parsedSentences: parsedSentences.filter(
						(_, index) => !indices.includes(index),
					),
				})),
			reorder: ({ from, to }: { from: number; to: number }) =>
				set(({ parsedSentences }) => {
					const cloned = [...parsedSentences];
					const item = parsedSentences[from];

					cloned.splice(from, 1);
					cloned.splice(to, 0, item);

					return { parsedSentences: cloned };
				}),
			swap: ({ from, to }: { from: number; to: number }) =>
				set(({ parsedSentences }) => {
					const cloned = [...parsedSentences];
					const fromItem = cloned[from];
					const toItem = cloned[to];

					cloned.splice(to, 1, fromItem);
					cloned.splice(from, 1, toItem);

					return { parsedSentences: cloned };
				}),
			setItem: (index: number, item: ParsedSentence) =>
				set(({ parsedSentences }) => {
					const cloned = [...parsedSentences];
					cloned[index] = item;
					return { parsedSentences: cloned };
				}),
			setItemProp: <
				K extends keyof ParsedSentenceEditable,
				U extends ParsedSentenceEditable[K],
			>(
				index: number,
				prop: K,
				value: U,
			) =>
				set(({ parsedSentences }) => {
					const cloned = [...parsedSentences];
					cloned[index] = { ...cloned[index], [prop]: value };
					return { parsedSentences: cloned };
				}),
			filter: (fn: (item: ParsedSentenceEditable, i: number) => boolean) => {
				set(({ parsedSentences }) => ({
					parsedSentences: parsedSentences.filter(fn),
				}));
			},
		},
		getLabellerSearchApi: async (opts?: TabLabellerInputProvided) => {
			const input = opts?.input || get().input;
			const offset = opts?.offsetPage || 0;

			if (input && input.sentence.length !== 0) {
				set({ loading: true });

				// preserve ~~ or ** for entire wildcard search, otherwise trim
				const trimmed =
					input.sentence.length === 2 && /(\*\*|~~)/.test(input.sentence)
						? input.sentence
						: input.sentence.trim();

				await fetch(constructEndpoint({ path: "labellerSearch" }), {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({
						...input.settings,
						sentence: trimmed,
						offset: offset,
					}),
				})
					.then((response) => {
						if (response.ok) return response.json();
						throw new Error(
							`Server response status @ ${response.status}. Check your browser network tab for traceback.`,
						);
					})
					.then((json) => {
						set({ loading: false, parsed: json });
						const parsedSentencesHandler = get().parsedSentencesHandler;
						parsedSentencesHandler.set(json.data); // for edited state of sentences
						set({ parsedSentencesOriginal: json.data }); // for original state of sentences
					})
					.catch((error) => {
						set({ loading: false, error: true });
						notifications.show({
							title: "Encountered some errors",
							message: error.message,
							position: "bottom-right",
						});
					});
			}
		},
		editLabellerItemsApi: async () => {
			set({ editing: true });

			const sentences = get().parsedSentences;
			const getLabellerSearchApi = get().getLabellerSearchApi;
			const fetchAvailableSourcesApi = get().fetchAvailableSourcesApi;
			const updateInputSettings = get().updateInputSettings;

			const result = await fetch(constructEndpoint({ path: "labellerSave" }), {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					edited: sentences
						.filter(({ edited }) => edited)
						.map(({ edited, removed, ...others }) => ({ ...others })),
					removed: sentences
						.filter(({ removed }) => removed)
						.map(({ edited, removed, ...others }) => ({ ...others })),
				}),
			})
				.then((response) => {
					if (response.ok) return response.json();
					throw new Error(
						`Server response status @ ${response.status}. Check your browser network tab for traceback.`,
					);
				})
				.then((_) => {
					set({ editing: false, editModeEnabled: false });
					getLabellerSearchApi();
					fetchAvailableSourcesApi();
					const availablePublisherSources = get().availablePublisherSources;
					updateInputSettings({ sources: availablePublisherSources });
					return true;
				})
				.catch((error) => {
					set({ editing: false });
					notifications.show({
						title: "Encountered some errors",
						message: error.message,
						position: "bottom-right",
					});
					return false;
				});

			return result;
		},
		parseNewLabellerItemsForUploadApi: async (value: string) => {
			if (!value.trim()) return null;

			set({ preuploading: true });

			const ingredients = value
				.split(/\r?\n/)
				.filter((str) => str.trim() !== "");

			const result = await fetch(
				constructEndpoint({ path: "labellerPreUpload" }),
				{
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({
						sentences: ingredients,
					}),
				},
			)
				.then((response) => {
					if (response.ok) return response.json();
					throw new Error(
						`Server response status @ ${response.status}. Check your browser network tab for traceback.`,
					);
				})
				.then((json) => {
					set({ preuploading: false });
					return json as ParsedSentenceEditable[];
				})
				.catch((error) => {
					set({ preuploading: false });
					notifications.show({
						title: "Encountered some errors",
						message: error.message,
						position: "bottom-right",
					});
					return null;
				});

			return result;
		},
		availablePublisherSources: [],
		fetchingAvailablePublisherSources: false,
		fetchAvailableSourcesApi: async () => {
			set({ fetchingAvailablePublisherSources: true });

			return await fetch(
				constructEndpoint({ path: "labellerAvailableSources" }),
				{
					method: "GET",
					headers: { "Content-Type": "application/json" },
				},
			)
				.then((response) => {
					if (response.ok) return response.json();
					throw new Error(
						`Server response status @ ${response.status}. Check your browser network tab for traceback.`,
					);
				})
				.then((json) => {
					set({
						availablePublisherSources: json,
						fetchingAvailablePublisherSources: false,
					});
					return json;
				})
				.catch((error) => {
					set({
						availablePublisherSources: [],
						fetchingAvailablePublisherSources: false,
					});
					notifications.show({
						title: "Encountered some errors",
						message: error.message,
						position: "bottom-right",
					});
					return [];
				});
		},
	})),
);
