// {{{EXTERNAL}}}
import React, {  } from "react"
import { Button } from "@mantine/core"
import { useShallow } from "zustand/react/shallow"
// {{{INTERNAL}}}
import { useTabTrainerStore } from "../../../domain"

export function ButtonInterruptModel() {

  const {
    training,
    onSendTrainInterrupt
  } = useTabTrainerStore(
    useShallow((state) => ({
      training: state.training,
      onSendTrainInterrupt: state.onSendTrainInterrupt
    })),
  )

  return training ? (
    <Button
      style={{ width: 150, height: 50 }}
      variant="dark"
      onClick={onSendTrainInterrupt}
    >
      Interrupt
    </Button>
  ) : null
}
