// {{{EXTERNAL}}}
import React, {  } from "react"
import { Box } from "@mantine/core"
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { Filler, ScrollableVirtualized, Sectionable } from "../../Shared/";
import { PrefabExamplesLabellerSource } from "../../PageTabLabeller";
import { Input, useTabLabellerStore } from "../../../domain";


export function ListParsedSentences() {

  const {
    parsed,
    parsedSentencesHandler,
    updateInput,
    getLabellerSearchApi
  } = useTabLabellerStore(
    useShallow((state) => ({
      parsed: state.parsed,
      parsedSentencesHandler: state.parsedSentencesHandler,
      updateInput: state.updateInput,
      getLabellerSearchApi: state.getLabellerSearchApi
    })),
  )

  return (
    <>
    {
      parsed ? (
      <ScrollableVirtualized
          style={{ height: "100%", width: "100%" }}
          labellerSentenceProps={{
            tasks: ["copy", "plain"],
            listable: true,
            handler: parsedSentencesHandler
          }}
          labellerProps={{
            handler: parsedSentencesHandler
          }}
      />
      ) : (
      <Filler text="Search for and edit ingredient labels or browse all from" illustration="sandwich">
        <Box mt="sm">
        <PrefabExamplesLabellerSource
          onClick={(abbr: string) => {
            const preFabInput = {
                sentence: "~~",
                settings: {
                  sources: [abbr],
                  caseSensitive: false,
                  labels: ["COMMENT",
                  "B_NAME_TOK",
                  "I_NAME_TOK",
                  "NAME_VAR",
                  "NAME_MOD",
                  "NAME_SEP" ,
                  "PREP",
                  "PUNC",
                  "PURPOSE",
                  "QTY",
                  "SIZE",
                  "UNIT",
                  "OTHER"],
                  wholeWord: false
              }
            } as Input
            updateInput(preFabInput)
            getLabellerSearchApi()
          }}
        />
        </Box>
      </Filler>
      )
    }
    </>
  )
}
