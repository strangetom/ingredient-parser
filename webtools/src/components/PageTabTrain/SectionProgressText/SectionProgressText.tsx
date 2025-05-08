// {{{EXTERNAL}}}
import React, {  } from "react"
import { Box, Center, ScrollArea, Stack, Text } from "@mantine/core"
import { useShallow } from "zustand/react/shallow"
// {{{INTERNAL}}}
import { useTabTrainerStore } from "../../../domain"

export function SectionProgressText() {

  const {
    events
  } = useTabTrainerStore(
    useShallow((state) => ({
      events: state.events
    })),
  )

  return (

        <Center bg="color-mix(in srgb,var(--fg), transparent 90%)" style={{ flexGrow: 1, height: "100%", width: "100%", borderRadius: "var(--xsmall-spacing)", overflow: "hidden" }}>
          <ScrollArea.Autosize w="100%" h="100%" type="always" scrollbars="y">
            <Stack gap={1}>
            {events.map(o => o.data).flat().map(str =>
              <Box pr="var(--medium-spacing)" px="var(--xsmall-spacing)" py="var(--xsmall-spacing)">
                <Text ff="monospace" variant="light" inline>{str}</Text>
              </Box>
            )}
            </Stack>
          </ScrollArea.Autosize>
        </Center>
  )
}
