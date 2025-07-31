// {{{EXTERNAL}}}
import React from "react"
import { create } from "zustand";
// {{{INTERNAL}}}
import { Link, Tab } from "../types";
import { MainTrainModel, MainTryParser, MainLabeller } from "../../components";
// {{{ASSETS}}}
import { IconAbc, IconSparkles, IconTags } from "@tabler/icons-react";
import { constructEndpoint } from "../api";
import { notifications } from "@mantine/notifications";

type PrecheckPackageMetadata = {
  checks: {
    failed: string[],
    passed: string[]
  },
  passed: boolean
}

interface AppShellState {
  loading: boolean;
  prechecking: boolean;
  error: boolean;
  success: boolean;
  openedSide: boolean;
  openSide: () => void;
  closeSide: () => void;
  toggleSide: () => void;
  openedNav: boolean;
  openNav: () => void;
  closeNav: () => void;
  toggleNav: () => void;
  tabs: Tab[];
  links: Link[];
  currentTab: Tab;
  setCurrentTab: (tab: Tab) => void;
  fetchPreCheck: () => void;
  precheckValid: boolean;
  precheckPackages: PrecheckPackageMetadata
}

export const useAppShellStore = create<AppShellState>((set) => ({
  loading: false,
  prechecking: false,
  error: false,
  success: false,
  openedSide: false,
  openSide: () => set({ openedSide: true }),
  closeSide: () => set({ openedSide: false }),
  toggleSide: () => set((state) => ({ openedSide: !state.openedSide })),
  openedNav: true,
  openNav: () => set({ openedNav: true }),
  closeNav: () => set({ openedNav: false }),
  toggleNav: () => set((state) => ({ openedNav: !state.openedNav })),
  tabs: [
    { id: 'parser', component: <MainTryParser />},
    { id: 'labeller', component: <MainLabeller />},
    { id: 'train', component: <MainTrainModel />}
  ],
  links:  [
    { link: '', label: 'Try the Parser', id: "parser", icon: IconAbc, disabled: false },
    { link: '', label: 'Browse & Label', id: "labeller", icon: IconTags, disabled: false },
    { link: '', label: 'Train the Model', id: "train", icon: IconSparkles, disabled: false }
  ],
  currentTab: { id: 'parser', component: <MainTryParser />},
  setCurrentTab: (tab: Tab) => set({ currentTab: tab }),
  fetchPreCheck: async () => {

    set({ prechecking: true })

    await fetch(
      constructEndpoint({ path: "precheck" }), {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })
      .then(response => {
        if (response.ok) return response.json()
        throw new Error(`Server response status @ ${response.status}. Check your browser network tab for traceback.`);
      })
      .then(json => {
        const valid = json.passed
        set({ prechecking: false, precheckValid: valid, precheckPackages: json })
      })
      .catch(error => {
        set({ loading: false })
        notifications.show({
          title: 'Encountered some errors',
          message: error.message,
          position: 'bottom-right'
        })
      })
  },
  precheckValid: false,
  precheckPackages: {
    checks: {
      failed: [],
      passed: []
    },
    passed: false
  }
}))
