// {{{EXTERNAL}}}
import React from 'react';
import { Box } from '@mantine/core';
import cx from 'clsx';
// {{{STYLES}}}
import { default as classes } from "./ActionBar.module.css"

export interface ActionBarProps  {
  children?: React.ReactNode;
  grow?: boolean
}

export function ActionBar(props: ActionBarProps) {

  const {
    children,
    grow = false,
    ...others
  } = props


   return (
     <Box {...others} className={cx(classes.root, { [classes.grow]: grow })}>
         <Box className={classes.groupings}>
           {children}
       </Box>
     </Box>
   )
 }
