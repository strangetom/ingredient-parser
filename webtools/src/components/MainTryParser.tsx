// {{{EXTERNAL}}}

import { useShallow } from "zustand/react/shallow";
import { useTabParserStore } from "../domain";
// {{{INTERNAL}}}
import {
  ButtonLabellerDefinitions,
  ButtonSubmit,
  InputSubmit,
  TableParsedResults,
  TableParsedSentence,
} from "./PageTabParser";
import { Sectionable } from "./Shared";

export function MainTryParser() {
  const { parsed } = useTabParserStore(
    useShallow((state) => ({
      parsed: state.parsed,
    })),
  );

  return (
    <Sectionable>
      <Sectionable.ActionBar position="top">
        <InputSubmit style={{ flexBasis: "100%" }} />
        <Sectionable.ActionBarSubGrouping>
          <ButtonSubmit />
          <ButtonLabellerDefinitions />
        </Sectionable.ActionBarSubGrouping>
      </Sectionable.ActionBar>

      <Sectionable.Section
        padded
        bordered
        border="bottom"
        mounted={Boolean(parsed)}
      >
        <TableParsedSentence />
      </Sectionable.Section>

      <Sectionable.Section grow padded>
        <TableParsedResults />
      </Sectionable.Section>
    </Sectionable>
  );
}
