import { notifications } from "@mantine/notifications";
import { io, type Socket } from "socket.io-client";
import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import { constructEndpoint } from "../api";
import type {
	AlgoVariant,
	InputTrainer,
	InputTrainerGridSearch,
	InputTrainerTask,
	Json,
	TrainerMode,
} from "../types";
import { validateJson } from "../utils";

interface ServerToClientEvents {
	trainer: (payload: EventLog) => void;
	status: (payload: EventLog) => void;
}

interface ClientToServerEvents {
	train: (payload: Json) => void;
}

type EventLog = {
	data: string[];
	indicator: string;
	message?: string;
};

interface TabTrainerState {
	input: InputTrainer;
	updateInput: (partial: Partial<InputTrainer>) => void;
	inputGridSearch: InputTrainerGridSearch;
	updateInputGridSearch: (partial: Partial<InputTrainerGridSearch>) => void;
	sanitizeAlgosInputGridSearch: () => Partial<InputTrainerGridSearch>;
	mode: TrainerMode;
	updateMode: (mode: TrainerMode) => void;
	connected: boolean;
	indicator: string;
	training: boolean;
	optimisticCacheReset: boolean;
	events: EventLog[];
	socket: Socket<ServerToClientEvents, ClientToServerEvents>;
	onReceiveConnect: () => void;
	onReceiveDisconnect: () => void;
	onReceiveStatus: (event: EventLog) => void;
	onReceiveTrainProgress: (event: EventLog) => void;
	onSendTrainRun: (category: InputTrainerTask) => void;
}

export const useTabTrainerStore = create(
	subscribeWithSelector<TabTrainerState>((set, get) => ({
		input: {
			sources: ["nyt", "cookstr", "allrecipes", "bbc", "tc"],
			split: 0.2,
			seed: Math.floor(Math.random() * 1_000_000_001),
			combineNameLabels: false,
			html: false,
			detailed: false,
			confusion: false,
			runsCategory: "single",
			runs: 2,
			processes: (window.navigator.hardwareConcurrency || 2) - 1,
			debugLevel: 0, // 0: logging.INFO, 1: logging.DEBUG
		},
		updateInput: (partial: Partial<InputTrainer>) =>
			set(({ input }) => ({ input: { ...input, ...partial } })),
		inputGridSearch: {
			combineNameLabels: false,
			sources: ["nyt", "cookstr", "allrecipes", "bbc", "tc"],
			split: 0.2,
			seed: Math.floor(Math.random() * 1_000_000_001),
			processes: (window.navigator.hardwareConcurrency || 2) - 1,
			algos: ["lbfgs"],
			algosGlobalParams: "{}",
			algosLBFGSParams: "{}",
			algosAPParams: "{}",
			algosL2SGDParams: "{}",
			algosPAParams: "{}",
			algosAROWParams: "{}",
			debugLevel: 0, // 0: logging.INFO, 1: logging.DEBUG
		},
		updateInputGridSearch: (partial: Partial<InputTrainerGridSearch>) =>
			set(({ inputGridSearch }) => ({
				inputGridSearch: { ...inputGridSearch, ...partial },
			})),
		sanitizeAlgosInputGridSearch: () => {
			const { inputGridSearch } = get();
			const {
				algos,
				algosGlobalParams,
				algosAPParams,
				algosAROWParams,
				algosL2SGDParams,
				algosLBFGSParams,
				algosPAParams,
			} = inputGridSearch;

			const gridsearchSanitizer = (params: string, variant: AlgoVariant) => {
				const clonedStubGlobal = ["global", ...algos];
				const isIncludedAndValid =
					clonedStubGlobal.includes(variant) &&
					validateJson(params, JSON.parse);
				return (isIncludedAndValid && params) || undefined;
			};

			const inputGridSearchResolved = {
				...inputGridSearch,
				algosGlobalParams: gridsearchSanitizer(algosGlobalParams, "global"),
				algosAPParams: gridsearchSanitizer(algosAPParams, "ap"),
				algosAROWParams: gridsearchSanitizer(algosAROWParams, "arow"),
				algosL2SGDParams: gridsearchSanitizer(algosL2SGDParams, "l2sgd"),
				algosLBFGSParams: gridsearchSanitizer(algosLBFGSParams, "lbfgs"),
				algosPAParams: gridsearchSanitizer(algosPAParams, "pa"),
			};

			return inputGridSearchResolved;
		},
		mode: "trainer" as TrainerMode,
		updateMode: (mode: TrainerMode) => set({ mode: mode }),
		connected: false,
		indicator: "Connecting",
		optimisticCacheReset: false,
		training: false,
		socket: io(
			constructEndpoint({ path: "trainerConnect", isWebSocket: true }),
			{
				cors: {
					origin: constructEndpoint({
						path: "trainerConnect",
						isWebSocket: true,
					}),
				},
			},
		),
		events: [],
		onReceiveConnect: () => {
			set({ indicator: "Connected", connected: true });
		},
		onReceiveDisconnect: () => {
			set({ indicator: "Disconnected", connected: false, training: false });
		},
		onReceiveStatus: (event: EventLog) => {
			set({ indicator: event.indicator });
			if (event.indicator === "Completed") {
				set({ training: false, optimisticCacheReset: true });
				notifications.show({
					title: "Training completed",
					message: event.message || null,
					position: "bottom-right",
				});
			} else if (event.indicator === "Error") {
				set({ training: false });
				notifications.show({
					title: "Training encountered error",
					message: event.message || null,
					position: "bottom-right",
					autoClose: false,
				});
			}
		},
		onReceiveTrainProgress: (event: EventLog) => {
			set((previous) => ({ events: [...previous.events, event] }));
		},
		onSendTrainRun: (task: InputTrainerTask) => {
			const socket = get().socket;
			const connected = get().connected;
			if (connected) {
				set({ events: [], training: true });

				const { input, sanitizeAlgosInputGridSearch } = get();
				const inputGridSearchSanitized = sanitizeAlgosInputGridSearch();

				if (task === "training") {
					socket.emit("train", {
						task: "training",
						...input,
					});
				} else if (task === "gridsearch") {
					socket.emit("train", {
						task: "gridsearch",
						...inputGridSearchSanitized,
					});
				} else {
					set({ training: false });
				}
			} else {
				notifications.show({
					title: "Not connected, web socket server is not active",
					message: null,
					position: "bottom-right",
				});
			}
		},
	})),
);
