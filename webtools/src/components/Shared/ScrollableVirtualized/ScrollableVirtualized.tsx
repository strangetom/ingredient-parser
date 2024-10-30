// {{{EXTERNAL}}}
import React, { useCallback, useRef} from "react"
import { UseListStateHandlers } from "@mantine/hooks";
import { List as ListVirtual, AutoSizer } from 'react-virtualized';
// {{{INTERNAL}}}
import { LabellerSentence, LabellerSentenceProps, Scrollable, ScrollableProps } from "../"
import { Box, MantineStyleProp } from "@mantine/core";
// {{{STYLES}}}

export interface ScrollableVirtualizedProps extends ScrollableProps {
  items: any[];
  handler?: UseListStateHandlers<any>,
  labellerSentenceProps?: Omit<LabellerSentenceProps, 'tokens' | 'sentence'>
}

export function ScrollableVirtualized({
  items,
  handler,
  labellerSentenceProps = {
    labellerProps: {
      editMode: true
    },
    listable: true,
    tasks: ["remove", "copy"]
  },
  ...others
}: ScrollableVirtualizedProps) {

  const sentenceListRenderer = useCallback(function({
    index,
    style
  }: {
    index: number,
    style: any
  }) {
    return (
      <LabellerSentence
        {...labellerSentenceProps}
        style={style}
        key={"labeller-sentence-" + index}
        identifier={items![index].id}
        tokens={items![index].tokens}
        sentence={items![index].sentence}
        handler={handler}
        w="100%"
      />
    );
  }, [items])

  return (
    <Box {...others}>
      <AutoSizer>
      {({ width, height }) => (
        <ListVirtual
          width={width}
          height={height}
          rowCount={items.length}
          rowHeight={72}
          rowRenderer={sentenceListRenderer}
        />
      )}
      </AutoSizer>
    </Box>
  )
}
