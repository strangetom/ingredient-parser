import { create } from "zustand";
import { io, Socket } from 'socket.io-client'
import { subscribeWithSelector } from "zustand/middleware";
import { constructEndpoint } from "../api";
import { notifications } from '@mantine/notifications';
import { InputTrainer, InputTrainerTask, InputTrainerGridSearch, TrainerMode } from "../types";

type EventLog = {
  data: string[];
  indicator: string;
  message?: string;
}

interface TabTrainerState {
  input: InputTrainer;
  updateInput: (partial: Partial<InputTrainer>) => void;
  inputGridSearch: InputTrainerGridSearch;
  updateInputGridSearch: (partial: Partial<InputTrainerGridSearch>) => void;
  mode: TrainerMode;
  updateMode: (mode: TrainerMode) => void;
  connected: boolean;
  indicator: string;
  training: boolean;
  optimisticCacheReset: boolean;
  events: EventLog[];
  socket: Socket<any, any>
  onReceiveConnect: () => void,
  onReceiveDisconnect: () => void,
  onReceiveStatus: (event: EventLog) => void,
  onReceiveTrainProgress: (event: EventLog) => void,
  onSendTrainRun: (category: InputTrainerTask) => void,
  /*onSendTrainInterrupt: () => void;*/
}

export const useTabTrainerStore =
  create(
    subscribeWithSelector<TabTrainerState>(
        (set, get) => ({
          input: {
            sources: ["nyt","cookstr", "allrecipes", "bbc", "tc", "saveur"],
            split: 0.2,
            seed: Math.floor(Math.random() * 1_000_000_001),
            combine_name_labels: false,
            html: false,
            detailed: false,
            confusion: false,
            runsCategory: 'single',
            runs: 2,
            processes: (window.navigator.hardwareConcurrency || 2) - 1,
            debugLevel: 0  // 0: logging.INFO, 1: logging.DEBUG
          },
          updateInput: (partial: Partial<InputTrainer>) =>
            set(
              ({ input }) =>({ input: { ...input, ...partial } })
            )
          ,
          inputGridSearch: {
            combine_name_labels: false,
            sources: ["nyt","cookstr", "allrecipes", "bbc", "tc", "saveur"],
            split: 0.2,
            seed: Math.floor(Math.random() * 1_000_000_001),
            processes: (window.navigator.hardwareConcurrency || 2) - 1,
            algos: ['lbfgs'],
            algosGlobalParams: '{}',
            keepModels: false,
            debugLevel: 0  // 0: logging.INFO, 1: logging.DEBUG
          },
          updateInputGridSearch: (partial: Partial<InputTrainerGridSearch>) =>
            set(
              ({ inputGridSearch }) =>({ inputGridSearch: { ...inputGridSearch, ...partial } })
            )
          ,
          mode: "trainer",
          updateMode: (mode: TrainerMode) => set({ mode: mode}),
          connected: false,
          indicator: "Connecting",
          optimisticCacheReset: false,
          training: false,
          socket:  io(constructEndpoint({ path: "trainerConnect", isWebSocket: true }), {
            cors: {
              origin: constructEndpoint({ path: "trainerConnect", isWebSocket: true }),
            },
          }),
          events: [],
          onReceiveConnect: () => {
            set({ indicator: "Connected", connected: true });
          },
          onReceiveDisconnect: () => {
            set({ indicator: "Disconnected", connected: false, training: false });
          },
          onReceiveStatus: (event: EventLog) => {
            set({ indicator: event.indicator });
            if(event.indicator === 'Completed'){
              set({ training: false, optimisticCacheReset: true });
              notifications.show({
                title: 'Training completed',
                message: event.message || null,
                position: 'bottom-right'
              })
            }
            /*
            else if(event.indicator === 'Interrupted'){
              set({ training: false });
              notifications.show({
                title: 'Training interrupt',
                message: event.message || null,
                position: 'bottom-right'
              })
            }
             */
            else if(event.indicator === 'Error'){
              set({ training: false });
              notifications.show({
                title: 'Training encountered error',
                message: event.message || null,
                position: 'bottom-right',
                autoClose: false
              })
            }
          },
          onReceiveTrainProgress: (event: EventLog) => {
            set((previous) => ({ events: [...previous.events, event] }));
          },
          onSendTrainRun: (task: InputTrainerTask) => {
            const socket = get().socket
            const connected = get().connected
            if (connected) {
              set({ events: [], training: true })

              if (task === 'training') {
                socket.emit("train", {
                  task: "training",
                  ...get().input
                });
              }
              else if (task === 'gridsearch') {
                socket.emit("train", {
                  task: "gridsearch",
                  ...get().inputGridSearch
                });
              }
              else {
                set({ training: false })
              }
            } else {
              notifications.show({
                title: 'Not connected, web socket server is not active',
                message: null,
                position: 'bottom-right'
              })
            }
          },
          /*
          onSendTrainInterrupt() {
            const socket = get().socket
            const connected = get().connected
            if (connected) {
              socket.emit("interrupt", {});
            } else {
              notifications.show({
                title: 'Not connected, web socket server is not active',
                message: null,
                position: 'bottom-right'
              })
            }
          }
           */
        })
      )
  )
