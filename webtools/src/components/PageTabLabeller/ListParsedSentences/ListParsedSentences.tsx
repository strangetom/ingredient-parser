// {{{EXTERNAL}}}
import React, { useEffect } from "react"
import { Affix, Box } from "@mantine/core"
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { Filler, ScrollableVirtualized } from "../../Shared/";
import { PrefabExamplesLabellerSource } from "../../PageTabLabeller";
import { InputTabLabeller, useTabLabellerStore } from "../../../domain";


export function ListParsedSentences() {

  const {
    editModeEnabled,
    parsed,
    parsedSentencesOriginal,
    parsedSentences,
    parsedSentencesHandler,
    updateInput,
    getLabellerSearchApi
  } = useTabLabellerStore(
    useShallow((state) => ({
      editModeEnabled: state.editModeEnabled,
      parsed: state.parsed,
      parsedSentencesOriginal: state.parsedSentencesOriginal,
      parsedSentences: state.parsedSentences,
      parsedSentencesHandler: state.parsedSentencesHandler,
      updateInput: state.updateInput,
      getLabellerSearchApi: state.getLabellerSearchApi
    })),
  )

  const onClickPreFabHandler = (abbr: string) => {
    const preFabInput = {
        sentence: "~~",
        settings: {
          sources: [abbr],
          caseSensitive: false,
          labels: [
            "COMMENT",
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
            "OTHER"
          ],
          wholeWord: false
      }
    } as InputTabLabeller
    updateInput(preFabInput)
    getLabellerSearchApi()
  }

  return (
    <>

    {
      parsed ? (
        <>
            {editModeEnabled && (
              <ScrollableVirtualized
                style={{ height: "100%", width: "100%" }}
                parsedSentencesProvided={parsedSentences}
                parsedSentencesProvidedHandler={parsedSentencesHandler}
                labellerSentenceProps={{
                  tasks: ["copy", "remove", "plain"],
                  listable: true
                }}
                labellerProps={{
                  editMode: true
                }}
              />
            )}

            {!editModeEnabled && (
              <ScrollableVirtualized
                style={{ height: "100%", width: "100%" }}
                parsedSentencesProvided={parsedSentencesOriginal}
                parsedSentencesProvidedHandler={{}}
                labellerSentenceProps={{
                  tasks: ["copy", "plain"],
                  listable: true
                }}
                labellerProps={{
                  editMode: false
                }}
              />)}
        </>
      ) : (
      <Filler text="Search for and edit ingredient labels or browse all from" illustration="sandwich">
        <Box mt="sm">
          <PrefabExamplesLabellerSource
            onClick={onClickPreFabHandler}
          />
        </Box>
      </Filler>
      )
    }
    </>
  )
}
