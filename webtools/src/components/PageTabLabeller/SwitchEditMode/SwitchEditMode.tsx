import { Box, Button, Group, Modal, Switch } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import type React from "react";
import { useShallow } from "zustand/react/shallow";
import { useTabLabellerStore } from "../../../domain";

export function SwitchEditMode() {
  const {
    loading,
    editing,
    editModeEnabled
  } = useTabLabellerStore(
    useShallow((state) => ({
      loading: state.loading,
      editing: state.editing,
      editModeEnabled: state.editModeEnabled
    })),
  );

  const onChangeHandler =
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const { setEditModeEnabled, hasUnsavedChanges, setUnsavedChangesModalOpen } =
        useTabLabellerStore.getState();
      if (hasUnsavedChanges() && !event.currentTarget.checked) {
        setUnsavedChangesModalOpen(true);
        const { setUnsavedChangesFnCallback } = useTabLabellerStore.getState();
        const fnCallback = () => {
          const { parsedSentencesOriginal, parsedSentencesHandler } = useTabLabellerStore.getState();
          parsedSentencesHandler.set(parsedSentencesOriginal)
          setEditModeEnabled(false);
        }
        setUnsavedChangesFnCallback(fnCallback)
      } else {
        setEditModeEnabled(event.currentTarget.checked);
      }
    }


  return (
    <Switch
      label="Enable editing"
      checked={editModeEnabled}
      onChange={onChangeHandler}
      disabled={loading || editing}
    />
  );
}
