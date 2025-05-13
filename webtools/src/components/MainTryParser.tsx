// {{{EXTERNAL}}}
import React, {  } from "react"
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { ButtonSubmit, InputSubmit, TableParsedResults, TableParsedSentence } from "./PageTabParser"
import { Sectionable } from "./Shared";
import { useTabParserStore } from "../domain";


export function MainTryParser() {

  const {
    parsed
  } = useTabParserStore(
    useShallow
      ((state) => ({
      parsed: state.parsed
    })),
  )

  return (
    <Sectionable>

      <Sectionable.ActionBar position="top">
        <InputSubmit style={{ flexBasis: "100%"}} />
        <Sectionable.ActionBarSubGrouping>
          <ButtonSubmit />
        </Sectionable.ActionBarSubGrouping>
      </Sectionable.ActionBar>

      <Sectionable.Section padded bordered border="bottom" mounted={Boolean(parsed)}>
        <TableParsedSentence />
      </Sectionable.Section>

      <Sectionable.Section grow padded>
        <TableParsedResults />
      </Sectionable.Section>

    </Sectionable>
  )
}
