// {{{EXTERNAL}}}
import React, { useEffect } from "react";
import { DrawerProps, Drawer, Box, Overlay } from "@mantine/core";
import { useListState, UseListStateHandlers } from "@mantine/hooks";
// {{{INTERNAL}}}
import { ActionBar } from "../ActionBar/ActionBar";
import { ScrollableVirtualized } from "../ScrollableVirtualized";
// {{{STYLES}}}
import { default as classes } from "./EditSheet.module.css"

interface EditSheetProps extends DrawerProps {
  items: any[];
  handler?: UseListStateHandlers<any>,
  footer: React.ReactNode;
}

export function EditSheet({
  footer = null,
  children,
  size = "md",
  position = "bottom",
  transitionProps = {
    transition: 'fade-up',
    duration: 150,
    timingFunction: 'ease'
  },
  opened,
  onClose,
  items,
  handler,
  overlayProps = { opacity: 1, backgroundOpacity: .86 },
  closeOnClickOutside = false,
  ...others
}: EditSheetProps) {

  return (

    <Drawer.Root
      {...others}
      opened={opened}
      onClose={onClose}
      size={size}
      position={position}
      transitionProps={transitionProps}
      closeOnClickOutside={closeOnClickOutside}
    >

      <Drawer.Overlay {...overlayProps} />

      <Drawer.Content className={classes.content}>
          <Box className={classes.inner}>
            <ScrollableVirtualized
              items={items}
              handler={handler}
              className={classes.scrollarea}
            />
            <ActionBar>
              {footer}
            </ActionBar>
          </Box>
      </Drawer.Content>
    </Drawer.Root>
  )
}
