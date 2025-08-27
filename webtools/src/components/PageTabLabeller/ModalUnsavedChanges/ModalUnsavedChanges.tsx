import { Box, Button, Group, Modal, Switch } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import type React from "react";
import { useShallow } from "zustand/react/shallow";
import { useTabLabellerStore } from "../../../domain";

export function ModalUnsavedChanges() {

  const {
    unsavedChangesModalOpen,
    setUnsavedChangesModalOpen
  } = useTabLabellerStore(
    useShallow((state) => ({
      unsavedChangesModalOpen: state.unsavedChangesModalOpen,
      setUnsavedChangesModalOpen: state.setUnsavedChangesModalOpen
    })),
  );

  const onOkToProceedHandler = () => {
    const { unsavedChangesFnCallback, setEditModeEnabled } = useTabLabellerStore.getState();
    unsavedChangesFnCallback?.()
    setUnsavedChangesModalOpen(false);
    setEditModeEnabled(false)
  };

  return (
    <Modal
      opened={unsavedChangesModalOpen}
      onClose={() => setUnsavedChangesModalOpen(false)}
      title="Are you sure?"
    >
      <Box mt="md">
        You have edited some entries, but have not saved them. Go back to save these edits, or proceed anyway.
      </Box>
      <Group mt="md" justify="flex-end">
        <Button onClick={() => setUnsavedChangesModalOpen(false)} variant="dark">
          Go back
        </Button>
        <Button onClick={onOkToProceedHandler} variant="light">
          Yes, I'm sure
        </Button>
      </Group>
    </Modal>
  );
}
