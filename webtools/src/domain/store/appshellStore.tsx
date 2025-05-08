// {{{EXTERNAL}}}
import React from "react"
import { create } from "zustand";
// {{{INTERNAL}}}
import { Link, Tab } from "../types";
import { MainTrainModel, MainTryParser, MainLabeller } from "../../components";
// {{{ASSETS}}}
import { IconAbc, IconSparkles, IconTags } from "@tabler/icons-react";

interface AppShellState {
  loading: boolean;
  precheck: boolean;
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
}

export const useAppShellStore = create<AppShellState>((set) => ({
  loading: false,
  precheck: false,
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
    { link: '', label: 'Train Model', id: "train", icon: IconSparkles, disabled: false }
  ],
  currentTab: { id: 'parser', component: <MainTryParser />},
  setCurrentTab: (tab: Tab) => set({ currentTab: tab })
}))
