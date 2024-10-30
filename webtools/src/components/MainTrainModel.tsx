// {{{EXTERNAL}}}
import { Box, Button, Center, Code, Group, ScrollArea, Stack, Text } from "@mantine/core"
import React, { useCallback, useContext, useEffect, useRef, useState } from "react"
import { notifications } from "@mantine/notifications"
// {{{INTERNAL}}}
import { ActionBar } from "./Shared"
// {{{STYLES}}}

// {{{ASSETS}}}
import { IconExclamationCircle, IconExclamationMark } from "@tabler/icons-react"
import { RunModelContext } from "./Shared/Shell/Shell"

export function MainTrainModel() {


  const { status, setStatus, poller, socket } = useContext(RunModelContext)
  const outputRef = useRef<HTMLUListElement>(null)
  const errorRef = useRef<HTMLDivElement>(null)

  const onRunHandler = useCallback(() => {

    if (!socket!.current) return;
    socket!.current.send("train")
    setStatus(status => ({ ...status, loading: true}))

    poller!.current = window.setInterval(() => {
        if(socket!.current) socket!.current.send("check")
      }, 5000
    )

  }, [socket!.current])

  const onCloseHandler = useCallback(() => {

    if (!socket!.current) return;
    socket!.current.send("interrupt")
    setStatus(status => ({ ...status, loading: false}))
    clearInterval(poller!.current)

  }, [socket!.current])

  return (
    <Box
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column"
      }}
    >

        <Box style={{ padding: "var(--small-spacing)", display: "flex", justifyContent: "flex-start", alignItems: "center", backgroundColor: "var(--fg-3)", color: "var(--bg-3)", gap: "var(--small-spacing)" }}>
            <IconExclamationCircle size={30} />
            <Stack gap="xs">
              <Text variant="dark" lh={1.3}>It takes about 12 minutes to train the on a laptop with an Intel Core 15-10300H and 16 GB of RAM. No GPU is required.</Text>
              <Text variant="dark" lh={1.3}>The equivalent train commands are fully configurable and accessible on the command line.</Text>
              <div>
                <div>
              <Code variant="dark">
                python train.py train --model parser --database train/data/training.sqlite3
              </Code>
              </div>
              <div>
              <Code variant="dark">
                python train.py train --model foundationfoods --database train/data/training.sqlite3
              </Code>
              </div>
              </div>
            </Stack>
        </Box>

        <ScrollArea  offsetScrollbars={true} scrollbars="y" type="always" styles={{ root: { width: "100%", flexGrow: 1, display: "flex"}}}>
          <ul id="output" ref={outputRef} />
          <div id="error" ref={errorRef} />
        </ScrollArea>


        <ActionBar>
          <span />
          <Group gap="var(--small-spacing)" wrap="nowrap">
            {status.loading && <Button style={{ width: 150, height: 50 }} variant="dark" onClick={onCloseHandler}>Stop</Button>}
            {!status.loading && <Button style={{ width: 150, height: 50 }} variant="dark" onClick={onRunHandler}>Run model</Button>}
          </Group>
        </ActionBar>

    </Box>
  )
}
