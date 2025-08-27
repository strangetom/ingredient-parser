// {{{EXTERNAL}}}
import { Box, type MantineStyleProp } from "@mantine/core";
import { useMemo } from "react";
import { AutoSizer, List as ListVirtual } from "react-virtualized";
// {{{INTERNAL}}}
import type { ParsedSentenceEditable, ParsedSentenceEditableHandler } from "../../../domain";
import {
  type LabellerProps,
  LabellerSentence,
  type LabellerSentenceProps,
  type ScrollableProps,
} from "../";

export interface ScrollableVirtualizedProps extends ScrollableProps {
  parsedSentencesProvided: ParsedSentenceEditable[];
  parsedSentencesProvidedHandler: ParsedSentenceEditableHandler;
  labellerSentenceProps?: Omit<LabellerSentenceProps, "tokens" | "sentence">;
  labellerProps?: Omit<LabellerProps, "token">;
}

export function ScrollableVirtualized({
  parsedSentencesProvided,
  parsedSentencesProvidedHandler,
  labellerSentenceProps,
  labellerProps,
  ...others
}: ScrollableVirtualizedProps) {
  const defaultLabellerSentenceProps = {
    listable: true,
    tasks: ["remove", "copy"],
    handler: parsedSentencesProvidedHandler,
    ...labellerSentenceProps,
  } as Omit<LabellerSentenceProps, "tokens" | "sentence">;

  const defaultLabellerProps = {
    editMode: false,
    handler: parsedSentencesProvidedHandler,
    ...labellerProps,
  } as LabellerProps;

  const sentenceListRenderer = useMemo(
    () =>
      ({ index, style }: { index: number; style: MantineStyleProp }) => (
        <LabellerSentence
          key={`labeller-sentence-${index}`}
          style={style}
          sentence={parsedSentencesProvided[index]}
          labellerProps={defaultLabellerProps}
          {...defaultLabellerSentenceProps}
        />
      ),
    [
      parsedSentencesProvided,
      defaultLabellerProps,
      defaultLabellerSentenceProps,
    ],
  );

  return (
    <Box {...others}>
      <AutoSizer>
        {({ width, height }) => (
          <ListVirtual
            width={width}
            height={height}
            rowCount={parsedSentencesProvided.length}
            rowHeight={92}
            rowRenderer={sentenceListRenderer}
          />
        )}
      </AutoSizer>
    </Box>
  );
}
