// {{{EXTERNAL}}}
import React, { useCallback } from "react"
import { Box, Button, Drawer, DrawerOverlayProps, DrawerProps, Group, Modal, Switch, Text } from "@mantine/core"
import { useDisclosure } from "@mantine/hooks";
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { useTabLabellerStore } from "../../../domain";
// {{{STYLES}}}
import classes from "./ButtonEdit.module.css"


export function SwitchEditMode() {

  const {
    editModeEnabled,
    parsed,
    setEditModeEnabled,
    parsedSentences
  } = useTabLabellerStore(
    useShallow((state) => ({
      editModeEnabled: state.editModeEnabled,
      parsed: state.parsed,
      setEditModeEnabled: state.setEditModeEnabled,
      parsedSentences: state.parsedSentences
    })),
  )

  if(!parsed) return null

  const [openedDialog, { open: openDialog, close: closeDialog }] = useDisclosure(false);

  const onChangeHandler = useCallback((event:  React.ChangeEvent<HTMLInputElement>) => {
    const hasEdited = parsedSentences.filter(({ edited, removed }) => edited || removed).length !== 0;
    if(hasEdited && !event.currentTarget.checked) {
      openDialog()
    }
    else {
      setEditModeEnabled(event.currentTarget.checked)
    }
  }, [parsedSentences])

  const onOkToProceedHandler = () => {
    closeDialog()
    setEditModeEnabled(false)
  }

  return (

    <>
      <Modal opened={openedDialog} onClose={closeDialog} title="Are you sure?">
        <Box mt="md">
          You have already edited some entries, and they will not be saved until you save changes.
        </Box>
        <Group mt="md" justify="flex-end">
          <Button onClick={closeDialog} variant="dark">
            Cancel
          </Button>
          <Button onClick={onOkToProceedHandler} variant="light">
            Yes, I'm sure
          </Button>
        </Group>
      </Modal>

      <Switch
        label="Enable editing"
        checked={editModeEnabled}
        onChange={onChangeHandler}
      />

    </>
  )
}
