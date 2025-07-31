// {{{EXTERNAL}}}
import React from "react"
// {{{INTERNAL}}}
import { Sectionable } from "./Shared"
import { ButtonInterruptModel, ButtonRunModel, ColorSwatchIndicator, SectionProgressText, SectionNotes } from "./PageTabTrain"
import { TimeElapsedIndicator } from "./PageTabTrain/TimeElapsedIndicator"
import { FetchAvailableSouceListener } from "./PageTabLabeller"

export function MainTrainModel() {

  return (
    <Sectionable>

      <FetchAvailableSouceListener />

      <Sectionable.ActionBar position="top">
        <Sectionable.ActionBarSubGrouping>
          <ColorSwatchIndicator />
          <TimeElapsedIndicator />
        </Sectionable.ActionBarSubGrouping>
        <Sectionable.ActionBarSubGrouping>
          {/**<ButtonInterruptModel />**/}
          <ButtonRunModel />
        </Sectionable.ActionBarSubGrouping>
      </Sectionable.ActionBar>

      <Sectionable.Section grow overflowHidden padded full>
        <SectionProgressText />
      </Sectionable.Section>

      <Sectionable.ActionBar position="bottom">
        <SectionNotes />
      </Sectionable.ActionBar>

    </Sectionable>
  )
}
