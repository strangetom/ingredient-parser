// {{{EXTERNAL}}}
import React from "react"
import { Button } from "@mantine/core"
import { useTabLabellerStore } from "../../../domain"
import { useShallow } from "zustand/react/shallow"
// {{{ASSETS}}}

export function ActionBarEditable() {

  const {
    editing,
    editLabellerItemsApi
  } = useTabLabellerStore(
    useShallow((state) => ({
      editing: state.editing,
      editLabellerItemsApi: state.editLabellerItemsApi
    })),
  )

  const onEditApiHandler = async () => {
    await editLabellerItemsApi();
  }

  return (
    <>
      <div />
      <Button
        variant="light"
        h={50}
        onClick={onEditApiHandler}
        loading={editing}
      >
        Save changes
      </Button>
    </>
  )
}
