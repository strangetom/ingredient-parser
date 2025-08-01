import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import { formattedCounterSeconds } from "../utils";


//  Extracted from Mantine useInterval hook
// https://github.com/mantinedev/mantine/blob/master/packages/@mantine/hooks/src/use-interval/use-interval.ts
export interface TabTrainerCounterState {
  seconds: number;
  setSeconds: (seconds: number) => void;
  secondsFormatted: string;
  intRef: number | null;
  fnRef: (() => void) | null;
  active: boolean;
  setActive: (value: boolean) => void;
  start: () => void;
  stop: () => void;
  reset: (seconds: number) => void;
}

export const useTabTrainerCounterStore = create(

  subscribeWithSelector<TabTrainerCounterState>(
    (set, get) => ({
      seconds: 0,
      setSeconds: (seconds: number) => set({
        seconds: seconds,
        secondsFormatted: formattedCounterSeconds(seconds)
      }),
      secondsFormatted: formattedCounterSeconds(0),
      intRef: null,
      fnRef: () => {
        set((state) => ({
          seconds: state.seconds + 1,
          secondsFormatted: formattedCounterSeconds(state.seconds + 1)
        }))
      },
      active: false,
      setActive: (value: boolean) => set({ active: value }),
      start: () => set((state) => {
        if (!state.active && (!state.intRef || state.intRef === -1)) {
          state.intRef = window.setInterval(state.fnRef!, 1000);
        }
        return ({ active: true })
      }),
      stop: () => set((state) => {
        window.clearInterval(state.intRef || -1);
        state.intRef = -1;
        return ({ active: false })
      }),
      reset: (seconds: number) => set({
        seconds: seconds,
        secondsFormatted: formattedCounterSeconds(seconds),
      }),
    })
  )
)

export async function subscribeCounterStore(training: boolean) {
  const state = useTabTrainerCounterStore.getState()
  if(training) {
    console.log("counter::training::on")
    state.start()
  }
  else {
    console.log("counter::training::off")
    state.stop()
    state.reset(0)
  }
}
