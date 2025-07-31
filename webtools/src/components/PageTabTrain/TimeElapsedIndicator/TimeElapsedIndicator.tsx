// {{{EXTERNAL}}}
import React, { useEffect, useMemo, useState } from "react"
import { ColorSwatch, Flex, Group, Paper, Text } from "@mantine/core"
import { useShallow } from "zustand/react/shallow"
// {{{INTERNAL}}}
import { useTabTrainerStore } from "../../../domain"
import { useInterval } from "@mantine/hooks";

function formatSecondsToTime(seconds: number) {
  const hh = String(Math.floor(seconds / 3600)).padStart(2, '0');
  const mm = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
  const ss = String(seconds % 60).padStart(2, '0');

  return `${hh}:${mm}:${ss}`;
}

function TimeElapsedInterval() {

  const [seconds, setSeconds] = useState(0);
  const interval = useInterval(() => setSeconds((s) => s + 1), 1000);

  useEffect(() => {
    interval.start();
    return () => {
      setSeconds(0)
      interval.stop();
    }
  }, []);

  return (
    <Paper w={120} bg="color-mix(in srgb,var(--fg), transparent 90%)" px="var(--medium-spacing)" py="var(--small-spacing)">
        <Text ta="center" variant="light">{formatSecondsToTime(seconds)}</Text>
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
