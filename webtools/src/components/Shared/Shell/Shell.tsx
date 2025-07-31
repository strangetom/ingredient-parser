// {{{EXTERNAL}}}
import React, { useMemo } from 'react';
import { ActionIcon, Anchor, AppShell, Flex, Group, Loader, Stack, Text, TooltipProps } from '@mantine/core';
import { useShallow } from 'zustand/react/shallow';
import cx from "clsx"
// {{INTERNAL}}
import { useAppShellStore, useTabTrainerStore } from '../../../domain';
import { TooltipExtended } from '../../MantineExtensions';
import { ShellWebSocketListener } from '../ShellWebSocketListener';
import { TabTitleListener } from '../TabTitleListener';
import { TabMultipleListener } from '../TabMultipleListener';
import { TabCloseListener } from '../TabCloseListener';
// {{{STYLES}}}
import { default as classes } from './Shell.module.css';
// {{{ASSETS}}}
import { IconArrowBarLeft, IconArrowBarRight, IconExternalLink } from "@tabler/icons-react"
import { ReactComponent as Logo } from "../../../assets/logo.svg"
import { TrainPreCheckListener } from '../TrainPreCheckListener';


export function Shell() {

  const {
    tabs,
    links,
    currentTab,
    setCurrentTab,
    openedNav,
    toggleNav
  } = useAppShellStore(
    useShallow((state) => ({
      tabs: state.tabs,
      links: state.links,
      currentTab: state.currentTab,
      setCurrentTab: state.setCurrentTab,
      openedNav: state.openedNav,
      toggleNav: state.toggleNav
    })),
  )

  const {
    training
  } = useTabTrainerStore(
    useShallow((state) => ({
      training: state.training
    })),
  )

  const linkables = links.map((item) => {

    const Wrapper = openedNav ? React.Fragment : TooltipExtended
    const wrapperProps = openedNav ? {} : { label: item.label, position: "right" } as TooltipProps

    return (
      <Wrapper {...wrapperProps}>
      <Anchor
      component='button'
      className={cx(
        classes.link,
        { [classes.linkCollapsed]: !openedNav }
      )}
      data-active={item.id === currentTab.id || undefined}
      key={item.label}
      disabled={item.disabled}
      onClick={(event) => {
        event.preventDefault();
        const match = tabs.find(tab => item.id === tab.id)
        if (!match) return;
        setCurrentTab(match);
      }}
    >
      <Flex justify={openedNav ? "flex-start" : "center"}>
        {training && item.id === 'train' ?  (
          <Loader
            size={25}
            color="var(--fg-3)"
            className={cx(
              classes.trainingIcon,
              { [classes.linkIconCollapsed]: !openedNav }
            )}
          />
        ): (
          <item.icon
            className={cx(
              classes.linkIcon,
              { [classes.linkIconCollapsed]: !openedNav }
            )}
            stroke={1.5}
          />
        )}
        {openedNav && <span>{item.label}</span>}
      </Flex>
    </Anchor>
      </Wrapper>
    )
  });

  const componentize = useMemo(() =>
    tabs.find(comp => comp.id === currentTab.id)!.component || null
  , [currentTab])

   return (
     <>

       <ShellWebSocketListener />
       <TabTitleListener />
       <TabCloseListener />
       <TabMultipleListener />
       <TrainPreCheckListener />

        <AppShell
          navbar={{
            width: openedNav ? 300 : 60,
            breakpoint: 0
          }}
          padding={0}
        >
          <AppShell.Navbar className={classes.appShellNavBar}>
            {
              openedNav ? (
                <Group justify="space-between">
                  <Group mb="md" wrap="nowrap">
                    <Logo style={{ width: 50, height: 50 }} />
                    <Stack>
                      <Text variant="light" lh={1}>Ingredient Parser</Text>
                      <Anchor td="none" variant="light" size="xs" mt="calc(-1*var(--xsmall-spacing))" lh={1} target='_blank' href="https://ingredient-parser.readthedocs.io">
                        <Group gap={3}>
                          <span>View the docs</span>
                          <IconExternalLink size={12} />
                        </Group>
                      </Anchor>
                    </Stack>
                  </Group>
                  <Flex mb="md">
                    <ActionIcon  variant="transparent-light" size={24} onClick={toggleNav}>
                      <IconArrowBarLeft size={24} />
                    </ActionIcon>
                  </Flex>
                </Group>
              ) : (
                <Flex mb="md" style={{ height: 50 }}>
                  <ActionIcon  variant="transparent-light" size={24} onClick={toggleNav}>
                    <IconArrowBarRight size={24} />
                  </ActionIcon>
                </Flex>
              )
            }
            {linkables}
          </AppShell.Navbar>
          <AppShell.Main>
            {componentize}
          </AppShell.Main>
        </AppShell>

     </>
   )
 }
