// {{{EXTERNAL}}}
import React, { forwardRef } from "react";
import { DrawerProps, Drawer, Box } from "@mantine/core";
// {{{INTERNAL}}}

// {{{STYLES}}}
import { default as classes } from "./Sheet.module.css"
import { useListState } from "@mantine/hooks";

interface SheetProps extends DrawerProps {
  footer: React.ReactNode;
}

export function Sheet({
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
  overlayProps = { opacity: 1, backgroundOpacity: .86 },
  closeOnClickOutside = false,
  ...others
}: SheetProps) {

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
            {children}
          </Box>
      </Drawer.Content>
    </Drawer.Root>
  )
}
