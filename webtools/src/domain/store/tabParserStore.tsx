import { create } from "zustand";
import { InputHistoryTabPaser, InputTabParser, ParsedTabParser } from "../types/tabParserTypes";
import { createJSONStorage, persist, subscribeWithSelector } from "zustand/middleware";
import { notifications } from '@mantine/notifications';
import { constructEndpoint } from "../api";

type TabParserInputProvided = {
  input?: InputTabParser,
  shouldAddToHistory?: boolean
} | undefined

interface TabParserState {
  loading: boolean;
  error: boolean;
  success: boolean;
  input: InputTabParser;
  updateInput: (partial: Partial<InputTabParser>) => void;
  parsed: ParsedTabParser | null;
  setParsed: (data: ParsedTabParser | null) => void;
  getParsedApi: (opts?: TabParserInputProvided) => void;
  history: InputHistoryTabPaser[];
  addHistory: (input: InputHistoryTabPaser) => void;
  clearHistory: () => void
}

export const useTabParserStore =
  create(
    subscribeWithSelector(
      persist<TabParserState>(
        (set, get) => ({
          loading: false,
          error: false,
          success: false,
          input: {
            sentence: "",
            discard_isolated_stop_words: true,
            expect_name_in_output: true,
            string_units: false,
            imperial_units: false,
            foundation_foods: false
          },
          updateInput: (partial: Partial<InputTabParser>) =>
            set(
              ({ input }) =>({ input: { ...input, ...partial } })
            )
          ,
          parsed: null,
          setParsed: (data: ParsedTabParser | null) => set({ parsed: data}),
          getParsedApi: async (opts?: TabParserInputProvided) => {
            const input = opts?.input || get().input

            if (input && input.sentence.trim().length !== 0) {
              set({ loading: true })

              await fetch(
                constructEndpoint({ path: "parser" }), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  ...input
                })
              })
                .then(response => {
                  if (response.ok) return response.json()
                  throw new Error(`Server response status @ ${response.status}. Check your browser network tab for traceback.`);
                })
                .then(json => {
                  set({ loading: false })
                  get().setParsed(json);
                  if(opts?.shouldAddToHistory) get().addHistory({ ...input, timestamp: new Date().toString() })
                })
                .catch(error => {
                  set({ loading: false })
                  notifications.show({
                    title: 'Encountered some errors',
                    message: error.message,
                    position: 'bottom-right'
                  })
                })
            }
          },
          history: [],
          addHistory: (input: InputHistoryTabPaser) => set(({ history }) => ({ history: [...history, input] })),
          clearHistory: () => set({ history: [] })
        }),
        {
          name: 'tabParser',
          storage: createJSONStorage(() => localStorage),
          partialize: (state) => ({ history: state.history }),
        }
      )
    )
  )
