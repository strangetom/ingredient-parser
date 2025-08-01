// {{{EXTERNAL}}}
import React, { useEffect, useMemo, useState } from "react"
import { ColorSwatch, Flex, Group, Paper, Text } from "@mantine/core"
import { useShallow } from "zustand/react/shallow"
// {{{INTERNAL}}}
import { useTabTrainerCounterStore, useTabTrainerStore } from "../../../domain"

function TimeElapsedInterval() {

  const {
    secondsFormatted
  } = useTabTrainerCounterStore(
    useShallow((state) => ({
      secondsFormatted: state.secondsFormatted
    })),
  )

  return (
    <Paper w={120} bg="color-mix(in srgb,var(--fg), transparent 90%)" px="var(--medium-spacing)" py="var(--small-spacing)">
        <Text ta="center" variant="light">{secondsFormatted}</Text>
    </Paper>
  )
}

export function TimeElapsedIndicator(){

  const {
    training
  } = useTabTrainerStore(
    useShallow((state) => ({
      training: state.training
    })),
  )

  return training ? <TimeElapsedInterval /> : null
}
