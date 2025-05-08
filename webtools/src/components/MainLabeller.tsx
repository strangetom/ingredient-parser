// {{{EXTERNAL}}}
import React from "react"
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { Sectionable } from "./Shared";
import { ButtonSearch, ActionBarPaginator, ButtonUpload, TextInputSubmit, ListParsedSentences, FetchAvailableSouceListener } from "./PageTabLabeller";
import { useTabLabellerStore } from "../domain";

export function MainLabeller() {

  const {
    parsed,
    parsedSentences
  } = useTabLabellerStore(
    useShallow((state) => ({
      parsed: state.parsed,
      parsedSentences: state.parsedSentences
    })),
  )

  return (
    <Sectionable>
      <FetchAvailableSouceListener />

      <Sectionable.ActionBar position="top">
        <TextInputSubmit style={{ flexBasis: "100%"}} />
        <Sectionable.ActionBarSubGrouping>
          <ButtonSearch />
          <ButtonUpload />
        </Sectionable.ActionBarSubGrouping>
      </Sectionable.ActionBar>

      <Sectionable.ActionBar mounted={Boolean(parsed) && parsedSentences.length !== 0}>
        <ActionBarPaginator />
      </Sectionable.ActionBar>

      <Sectionable.Section grow>
        <ListParsedSentences />
      </Sectionable.Section>

    </Sectionable>
  )
}
