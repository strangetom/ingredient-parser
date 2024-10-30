// {{{EXTERNAL}}}
import React, { useRef} from "react"
import { Box, ScrollArea, ScrollAreaProps } from "@mantine/core";
import cx from 'clsx';
// {{{STYLES}}}
import { default as classes } from "./Scrollable.module.css"

export interface ScrollableProps extends ScrollAreaProps {
  grow?: boolean;
  padded?: boolean;
}

export function Scrollable(props: ScrollableProps) {

  const {
    offsetScrollbars = true,
    scrollbars = "y",
    type = "always",
    children,
    grow = false,
    padded = false,
    ...others
  } = props

  const wrappable = padded ? (
    <Box className={classes.padded}>
      {children}
    </Box>
  ) : children

  return (
    <ScrollArea
      {...others}
      offsetScrollbars={offsetScrollbars}
      scrollbars={scrollbars}
      type={type}
      classNames={{ root: cx(classes.root, { [classes.grow]: grow }) }}
    >
      {wrappable}
    </ScrollArea>
  )
}
