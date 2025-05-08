// {{{EXTERNAL}}}
import React from "react"
import { Box, Code, Stack, Text } from "@mantine/core"
// {{{ASSETS}}}
import { IconExclamationCircle } from "@tabler/icons-react"

export function SectionNotes() {

  return (
    <div style={{width: "100%"}}>
      <Box style={{ padding: "var(--small-spacing)", display: "flex", justifyContent: "flex-start", alignItems: "center", backgroundColor: "var(--fg-3)", gap: "var(--small-spacing)", borderRadius: "var(--xsmall-spacing)" }}>
          <IconExclamationCircle size={30} color="var(--bg-2)"/>
          <Stack gap="xs">
            <Text variant="dark" lh={1.3}>It takes about 12 minutes to train the on a laptop with an Intel Core 15-10300H and 16 GB of RAM. No GPU is required.</Text>
            <Text variant="dark" lh={1.3}>The equivalent train commands are fully configurable and accessible on the command line.</Text>
            <div>
              <Box>
                <Code variant="dark">
                  python train.py train --model parser --database train/data/training.sqlite3
                </Code>
              </Box>
              <Box>
                <Code variant="dark">
                  python train.py train --model foundationfoods --database train/data/training.sqlite3
                </Code>
              </Box>
            </div>
          </Stack>
      </Box>
    </div>
  )
}
