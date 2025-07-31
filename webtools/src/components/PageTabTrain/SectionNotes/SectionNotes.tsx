// {{{EXTERNAL}}}
import React from "react"
import { Anchor, Box, Code, Stack, Text } from "@mantine/core"
// {{{ASSETS}}}
import { IconExclamationCircle } from "@tabler/icons-react"

export function SectionNotes() {

  return (
    <div style={{width: "100%"}}>
      <Box style={{ padding: "var(--small-spacing)", display: "flex", justifyContent: "flex-start", alignItems: "center", backgroundColor: "var(--fg-3)", gap: "var(--small-spacing)", borderRadius: "var(--xsmall-spacing)" }}>
          <Box h={30} w={30}>
            <IconExclamationCircle size={30} color="var(--bg-2)"/>
          </Box>
          <Stack gap="xs">
            <Text variant="dark" lh={1.3}>It takes about an hour to train the model using the all the available training data on a laptop with an Intel Core 15-10300H and 64 GB of RAM. You will not need 64 GB of RAM to train the model, 8 GB should be more than sufficient and less will probably work too. No GPU is required.</Text>
            <Text variant="dark" lh={1.3}>The equivalent commands are fully configurable and accessible on the default command line tool. Please view the full documentation for all available options and instructions <Anchor inline variant="dark" lh={1.3} target="_blank" href="https://ingredient-parser.readthedocs.io/en/latest/explanation/training.html">here</Anchor>.</Text>
            <Box>
              <Code variant="dark">
                python train.py train --model parser --database train/data/training.sqlite3
              </Code>
            </Box>
          </Stack>
      </Box>
    </div>
  )
}
