// {{{EXTERNAL}}}
import React, {  } from "react"
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { LabellerSentence, Sectionable } from "../../Shared";
import { ParsedSentenceEditable, useTabParserStore } from "../../../domain";

export function TableParsedSentence(){

  const {
    input,
    parsed
  } = useTabParserStore(
    useShallow((state) => ({
      input: state.input,
      parsed: state.parsed
    })),
  )

  return parsed ? (
      <LabellerSentence
        sentence={
          { id: "", labels: [], tokens: parsed.tokens, sentence: input.sentence, source: "-" } as ParsedSentenceEditable
        }
        labellerProps={{ marginalsMode: true, size: "large" }}
      />
  ) : null
}
