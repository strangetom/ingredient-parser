// {{{EXTERNAL}}}
import React, { useMemo } from "react"
import { ColorSwatch, Group, Paper, Text } from "@mantine/core"
import { useShallow } from "zustand/react/shallow"
// {{{INTERNAL}}}
import { useTabTrainerStore } from "../../../domain"

function ColorSwatchDot(){

  const {
    indicator
  } = useTabTrainerStore(
    useShallow((state) => ({
      indicator: state.indicator
    })),
  )

  const color = useMemo(() =>
    ({
      'Connected': 'var(--green)',
      'Training': 'var(--fg)',
      'Disconnected': 'var(--red)',
      'Interrupted': 'var(--red)',
      'Cancelled': 'var(--red)',
      'Error': 'var(--red)',
      'Completed': 'var(--green)',
    })[indicator] ?? 'var(--fg)'
  , [indicator])

  return (
    <ColorSwatch
      size={12}
      withShadow={false}
      color={color}
    />
  )
}

function ColorSwatchText(){

  const {
    indicator
  } = useTabTrainerStore(
    useShallow((state) => ({
      indicator: state.indicator
    })),
  )


  return (
    <Text variant="light">{indicator}</Text>
  )
}


export function ColorSwatchIndicator(){

  return (
    <Paper bg="color-mix(in srgb,var(--fg), transparent 90%)" px="var(--medium-spacing)" py="var(--small-spacing)">
    <Group gap="xs">
      <ColorSwatchDot />
      <ColorSwatchText />
    </Group>
    </Paper>
  )
}
