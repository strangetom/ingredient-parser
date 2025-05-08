// {{EXTERNAL}}
import React from "react"
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { ScrollableVirtualized } from "../../../../Shared";
import { useUploadNewLabellersStore } from "../../../../../domain";

export function StepTwo(){

  const {
    parsedSentences,
    parsedSentencesHandler
  } = useUploadNewLabellersStore(
    useShallow((state) => ({
      parsedSentences: state.parsedSentences,
      parsedSentencesHandler: state.parsedSentencesHandler
    })),
  )

  return (
    <ScrollableVirtualized
      style={{ flexGrow: 1, height:"100%", width: "100%", position: "relative"}}
      parsedSentencesProvided={parsedSentences}
      parsedSentencesProvidedHandler={parsedSentencesHandler}
      labellerProps={{ editMode: true }}
      labellerSentenceProps={{ tasks: ["copy", "plain", "remove"]}}
    />
  )
}
