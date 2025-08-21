// {{EXTERNAL}}
import type { FileWithPath } from "@mantine/dropzone";
import type { UseListStateHandlers } from "@mantine/hooks";
import { notifications } from "@mantine/notifications";
import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import { constructEndpoint } from "../api";
import type {
	ParsedSentence,
	ParsedSentenceEditable,
} from "../types/tabLabellerTypes";
// {{{INTERNAL}}}
import { defaultInputLabeller, useTabLabellerStore } from "./tabLabellerStore";

type AsyncPromiseFn<T> = (...args: T[]) => Promise<T>;
type AccessibleUploadNewLabellersState = Pick<
	UploadNewLabellersState,
	| "rawText"
	| "files"
	| "activeStep"
	| "parsedSentences"
	| "uploadOption"
	| "stepCallbackFns"
	| "importingRawText"
	| "publisherSource"
>;

export const TOTAL_UPLOAD_STEPS = 3;

interface UploadNewLabellersState {
	rawText: string;
	importingRawText: boolean;
	files: FileWithPath[] | null;
	uploadOption: string;
	activeStep: number;
	stepCallbackFns: Array<AsyncPromiseFn<boolean> | null>;
	onNextStepHandler: () => void;
	onPrevStepHandler: () => void;
	onIngredientSentenceEntryHandler: () => Promise<boolean>;
	setState: (values: Partial<AccessibleUploadNewLabellersState>) => void;
	resetState: () => void;
	parsedSentences: ParsedSentenceEditable[];
	parsedSentencesHandler: Omit<
		UseListStateHandlers<ParsedSentenceEditable>,
		"setState"
	> & { set: (items: ParsedSentenceEditable[]) => void };
	publisherSource: string | null;
	uploadingBulk: boolean;
	bulkUploadApi: () => Promise<boolean>;
}

const defaultUploadNewLabellersState = {
	rawText: "",
	importingRawText: false,
	publisherSource: null,
	files: null,
	activeStep: 0,
	uploadOption: "copy.paste" as const,
	stepCallbackFns: Array(TOTAL_UPLOAD_STEPS).fill(null),
	uploadingBulk: false,
};

export const useUploadNewLabellersStore = create(
	subscribeWithSelector<UploadNewLabellersState>((set, get) => ({
		rawText: defaultUploadNewLabellersState.rawText,
		importingRawText: defaultUploadNewLabellersState.importingRawText,
		files: defaultUploadNewLabellersState.files,
		uploadOption: defaultUploadNewLabellersState.uploadOption,
		activeStep: defaultUploadNewLabellersState.activeStep,
		stepCallbackFns: defaultUploadNewLabellersState.stepCallbackFns,
		onNextStepHandler: async () => {
			const stepCallbackFns = get().stepCallbackFns;
			const activeStep = get().activeStep;
			const setState = get().setState;

			const callback = stepCallbackFns[activeStep] || null;
			let callbackResultSuccess = false;
			if (callback && typeof callback === "function") {
				callbackResultSuccess = await callback();
			}

			const newActiveStep = (() => {
				const updatedStep =
					activeStep < TOTAL_UPLOAD_STEPS ? activeStep + 1 : activeStep;
				if (callback && typeof callback === "function" && callbackResultSuccess)
					return updatedStep;
				else if (
					callback &&
					typeof callback === "function" &&
					!callbackResultSuccess
				)
					return activeStep;
				else return updatedStep;
			})();

			setState({ activeStep: newActiveStep });
		},
		onPrevStepHandler: () => {
			const activeStep = get().activeStep;
			const setState = get().setState;

			const newActiveStep = activeStep > 0 ? activeStep - 1 : activeStep;
			setState({ activeStep: newActiveStep });
		},

		onIngredientSentenceEntryHandler: async () => {
			const rawText = get().rawText;
			const parsedSentencesHandler = get().parsedSentencesHandler;
			const parseNewLabellerItemsForUploadApi =
				useTabLabellerStore.getState().parseNewLabellerItemsForUploadApi;

			if (!rawText || rawText.length === 0) return false;
			const parsed = await parseNewLabellerItemsForUploadApi(rawText);
			if (!parsed) return false;
			parsedSentencesHandler.set(parsed);
			return true;
		},
		setState: (values: Partial<AccessibleUploadNewLabellersState>) =>
			set({ ...values }),
		resetState: () => set({ ...defaultUploadNewLabellersState }),
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
		publisherSource: defaultUploadNewLabellersState.publisherSource,
		uploadingBulk: defaultUploadNewLabellersState.uploadingBulk,
		bulkUploadApi: async () => {
			set({ uploadingBulk: true });

			const sentences = get().parsedSentences;
			const source = get().publisherSource;
			const fetchAvailableSourcesApi =
				useTabLabellerStore.getState().fetchAvailableSourcesApi;
			const getLabellerSearchApi =
				useTabLabellerStore.getState().getLabellerSearchApi;
			const inputSettings = useTabLabellerStore.getState().input.settings;
			const updateInput = useTabLabellerStore.getState().updateInput;
			const setParsed = useTabLabellerStore.getState().setParsed;
			const sentencesAmended = sentences.map((sentence) => ({
				...sentence,
				source: source,
			}));

			const result = await fetch(
				constructEndpoint({ path: "labellerBulkUpload" }),
				{
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify(sentencesAmended),
				},
			)
				.then((response) => {
					if (response.ok) return response.json();
					throw new Error(
						`Server response status @ ${response.status}. Check your browser network tab for traceback.`,
					);
				})
				.then(async () => {
					const availablePublisherSources = await fetchAvailableSourcesApi();

					if (source && availablePublisherSources.includes(source)) {
						const newInput = {
							input: {
								sentence: "~~",
								settings: { ...inputSettings, sources: [source] },
							},
							offsetPage: 0,
						};
						getLabellerSearchApi(newInput);
						updateInput(newInput.input);
					} else {
						setParsed(null);
						updateInput(defaultInputLabeller);
					}

					set({ uploadingBulk: false });

					notifications.show({
						title: "Upload successful",
						message: `Total of ${sentencesAmended.length} sentences added`,
						position: "bottom-right",
					});

					return true;
				})
				.catch((error) => {
					set({ uploadingBulk: false });
					notifications.show({
						title: "Encountered some errors",
						message: error.message,
						position: "bottom-right",
					});
					return false;
				});

			return result;
		},
	})),
);
