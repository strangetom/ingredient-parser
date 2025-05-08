// {{{EXTERNAL}}}
import React, {  } from "react"
import { Box, Button, Drawer, DrawerOverlayProps, DrawerProps, Group, Text } from "@mantine/core"
import { useDisclosure } from "@mantine/hooks";
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { Sectionable, ScrollableVirtualized } from "../../Shared";
import { useTabLabellerStore } from "../../../domain";
// {{{STYLES}}}
import classes from "./ButtonEdit.module.css"

interface EditSheetProps {
  opened: DrawerProps["opened"];
  onClose: DrawerProps["onClose"];
  footer?: React.ReactNode;
  drawerProps?: DrawerProps;
  children?: React.ReactNode;
}

export function EditSheet({
  footer = null,
  opened,
  onClose,
  children,
  drawerProps,
  ...others
}: EditSheetProps) {

  const defaultDrawerProps = {
    size: "lg",
    position: "bottom",
    transitionProps: {
      transition: 'fade-up',
      duration: 150,
      timingFunction: 'ease'
    },
    closeOnClickOutside: false,
    ...drawerProps
  } as Partial<DrawerProps>

  const defaultOverlayProps = {
    opacity: 1,
    backgroundOpacity: .86
  } as Partial<DrawerOverlayProps>

  const {
    parsedSentencesHandler
  } = useTabLabellerStore(
    useShallow((state) => ({
      parsedSentencesHandler: state.parsedSentencesHandler
    })),
  )

  return (

    <Drawer.Root
      {...others}
      opened={opened}
      onClose={onClose}
      {...defaultDrawerProps}
    >

      <Drawer.Overlay {...defaultOverlayProps} />

      <Drawer.Content className={classes.content}>
        <Box className={classes.inner}>
          <ScrollableVirtualized
            className={classes.scrollarea}
            labellerSentenceProps={{
              tasks: ["copy", "remove", "plain"],
              listable: true,
              handler: parsedSentencesHandler
            }}
            labellerProps={{
              editMode: true,
              handler: parsedSentencesHandler
            }}
          />
          {
            footer &&
            <Sectionable.ActionBar position="bottom">
              {footer}
            </Sectionable.ActionBar>
          }
        </Box>
      </Drawer.Content>
    </Drawer.Root>
  )
}


export function ButtonEdit() {

  const {
    editing,
    parsed,
    activePage,
    editLabellerItemsApi
  } = useTabLabellerStore(
    useShallow((state) => ({
      editing: state.editing,
      parsed: state.parsed,
      activePage: state.activePage,
      editLabellerItemsApi: state.editLabellerItemsApi
    })),
  )

  if(!parsed) return null

  const [ opened, { open, close }] = useDisclosure(false)

  // Handlers
  const onEditApiHandler = async () => {
    const result = await editLabellerItemsApi();
    if(result) close()
  }

  // Components
  const footer = (<>
    <Text variant="light">
        Editing page {activePage} of {Math.ceil(parsed.total / 250)}
    </Text>
    <Group>
      <Button variant="light" onClick={close} disabled={editing}>Cancel</Button>
      <Button variant="light" onClick={onEditApiHandler} loading={editing}>Save edits</Button>
    </Group>
  </>)

  return (
    <>

      <Button variant="light" onClick={open}>
        Enter edit mode
      </Button>

      <EditSheet
        footer={footer}
        opened={opened}
        onClose={close}
      />

    </>
  )
}
