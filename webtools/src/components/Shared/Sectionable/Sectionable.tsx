// {{{EXTERNAL}}}
import React from "react"
import { Box, BoxProps } from "@mantine/core";
import cx from 'clsx';
// {{{STYLES}}}
import { default as classes } from "./Sectionable.module.css"

export interface SectionableProps extends BoxProps {
  children: React.ReactNode;
  grow?: boolean;
  padded?: boolean;
  full?: boolean;
  bordered?: boolean;
  border?: "top" | "bottom" | "left" | "right"
}

export function Sectionable(props: SectionableProps) {

  const {
    grow = false,
    padded = false,
    bordered = false,
    full = false,
    border,
    children,
    ...others
  } = props

  const wrappable = padded ? (
    <Box
      className={cx(
        classes.padded,
        {
          [classes.full]: full,
        }
      )}
    >
      {children}
    </Box>
  ) : children

  return (
    <Box
      {...others}
      className={cx(
        classes.root,
        {
          [classes.grow]: grow,
          [classes.bordered]: bordered,
          [classes.full]: full,
        }
      )}
      data-bordered={(bordered && border) || undefined }
    >
      {wrappable}
    </Box>
  )
}
