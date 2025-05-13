// {{{EXTERNAL}}}
import React, { useCallback} from "react"
import { Box } from "@mantine/core";
import { List as ListVirtual, AutoSizer } from 'react-virtualized';
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { LabellerProps, LabellerSentence, LabellerSentenceProps, ScrollableProps } from "../"
import { useTabLabellerStore, ParsedSentenceEditable } from "../../../domain";

export interface ScrollableVirtualizedProps extends ScrollableProps {
  parsedSentencesProvided: ParsedSentenceEditable[];
  parsedSentencesProvidedHandler: any;
  labellerSentenceProps?: Omit<LabellerSentenceProps, 'tokens' | 'sentence'>,
  labellerProps?: LabellerProps
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
    ...labellerSentenceProps
  } as Omit<LabellerSentenceProps, 'tokens' | 'sentence'>

  const defaultLabellerProps = {
    editMode: false,
    handler: parsedSentencesProvidedHandler,
    ...labellerProps
  } as LabellerProps

  const sentenceListRenderer = useCallback(function({
    index,
    style
  }: {
    index: number,
    style: any
  }) {
    return (
      <LabellerSentence
        key={"labeller-sentence-" + index}
        style={style}
        sentence={parsedSentencesProvided[index]}
        labellerProps={defaultLabellerProps}
        {...defaultLabellerSentenceProps}
      />
    );
  }, [parsedSentencesProvided])

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
  )
}
