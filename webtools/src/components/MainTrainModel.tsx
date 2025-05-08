// {{{EXTERNAL}}}
import React from "react"
// {{{INTERNAL}}}
import { Sectionable } from "./Shared"
import { ButtonInterruptModel, ButtonRunModel, ColorSwatchIndicator, SectionProgressText, SectionNotes } from "./PageTabTrain"

export function MainTrainModel() {

  return (
    <Sectionable>

      <Sectionable.ActionBar position="top">
        <ColorSwatchIndicator />
        <Sectionable.ActionBarSubGrouping>
          <ButtonInterruptModel />
          <ButtonRunModel />
        </Sectionable.ActionBarSubGrouping>
      </Sectionable.ActionBar>

      <Sectionable.Section grow padded full>
        <SectionProgressText />
      </Sectionable.Section>

      <Sectionable.ActionBar position="bottom">
        <SectionNotes />
      </Sectionable.ActionBar>

    </Sectionable>
  )
}
