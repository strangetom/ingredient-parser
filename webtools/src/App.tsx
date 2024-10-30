// {{{EXTERNAL}}}
import React, { useState } from "react";
// {{{INTERNAL}}}
import { GlobalStyles } from "./Styles";
import { MainTryParser } from "./components/MainTryParser";
import { MainLabeller } from "./components/MainLabeller";
import { MainTrainModel } from "./components/MainTrainModel";
import { Shell } from "./components/Shared";
import { Tab } from "./components/Shared/Shell/Shell";
// {{{STYLES}}}

// {{{COLLECTIONS}}}


export default function App() {

  const tabs: Tab[] = [
    { id: 'parser', component: <MainTryParser />},
    { id: 'labeller', component: <MainLabeller />},
    { id: 'train', component: <MainTrainModel />}
  ]

  return (
    <GlobalStyles>
      <Shell tabs={tabs}/>
    </GlobalStyles>
  )
}
