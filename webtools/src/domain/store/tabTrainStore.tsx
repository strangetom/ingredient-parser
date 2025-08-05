import { create } from "zustand";
import { io, Socket } from 'socket.io-client'
import { subscribeWithSelector } from "zustand/middleware";
import { constructEndpoint } from "../api";
import { notifications } from '@mantine/notifications';
import { InputTrainer } from "../types";

type EventLog = {
  data: string[];
  indicator: string;
  message?: string;
}

interface TabTrainerState {
  input: InputTrainer;
  updateInput: (partial: Partial<InputTrainer>) => void;
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
  onSendTrainRun: () => void,
  /*onSendTrainInterrupt: () => void;*/
}

export const useTabTrainerStore =
  create(
    subscribeWithSelector<TabTrainerState>(
        (set, get) => ({
          input: {
            model: 'parser',
            sources: ["nyt","cookstr", "allrecipes", "bbc", "tc", "saveur"],
            split: 0.2,
            seed: Math.floor(Math.random() * 1_000_000_001),
            html: false,
            detailed: false,
            confusion: false
          },
          updateInput: (partial: Partial<InputTrainer>) =>
            set(
              ({ input }) =>({ input: { ...input, ...partial } })
            )
          ,
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
          onSendTrainRun: () => {
            const socket = get().socket
            const connected = get().connected
            if (connected) {
              set({ events: [], training: true })
              socket.emit("train", {
                ...get().input
              });
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
