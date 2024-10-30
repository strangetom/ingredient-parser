// {{{EXTERNAL}}}
import React, { createContext, useEffect, useMemo, useRef, useState } from 'react';
import { Anchor, AppShell, Badge, Burger, Divider, Flex, Group, List, Loader, Title, Tooltip } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
// {{{ASSETS}}}
import { ReactComponent as Logo } from "../../../assets/logo.svg"
import { Icon, IconAbc, IconHelp, IconProps, IconQuestionMark, IconSparkles, IconTags } from "@tabler/icons-react"
// {{{STYLES}}}
import { default as classes } from './Shell.module.css';
import { notifications } from '@mantine/notifications';

const linkIdentifiers = [
  "parser",
  "labeller",
  "train"
] as const;

export type LinkIdentifier = typeof linkIdentifiers[number];

export interface Link {
  link: string;
  label: string;
  id: LinkIdentifier;
  icon: React.ForwardRefExoticComponent<IconProps & React.RefAttributes<Icon>>,
  loading?: boolean;
  disabled: boolean;
}

export const links: Link[] = [
  { link: '', label: 'Try Parser', id: "parser", icon: IconAbc, disabled: false },
  { link: '', label: 'Adjust Labeller', id: "labeller", icon: IconTags, disabled: false },
  { link: '', label: 'Train Model', id: "train", icon: IconSparkles, disabled: false }
];

interface ShellContextProps {
  links: Link[],
  active: LinkIdentifier,
  setActive: React.Dispatch<React.SetStateAction<LinkIdentifier>>,
  precheckPassed: boolean,
  setPrecheckPassed: React.Dispatch<React.SetStateAction<boolean>>
}

export const ShellContext = createContext<ShellContextProps>({
  links: links,
  active: 'parser',
  setActive: () => undefined,
  precheckPassed: false,
  setPrecheckPassed: () => undefined
});

export type Tab = {
  id: LinkIdentifier,
  component: React.ReactNode
}

type RunModelStatus = {
  loading: boolean,
  precheck: boolean;
  error: boolean;
  success: boolean;
}

export interface RunModelContextProps {
  status: RunModelStatus,
  setStatus: React.Dispatch<React.SetStateAction<RunModelStatus>>,
  socket: React.MutableRefObject<WebSocket> | null,
  poller: React.MutableRefObject<ReturnType<typeof setInterval> | undefined> | null
}

export const defaultRunModelProps = {
  loading: false,
  precheck: false,
  error: false,
  success: false
}

export const RunModelContext = createContext<RunModelContextProps>({
  status: defaultRunModelProps,
  setStatus: () => undefined,
  socket: null,
  poller: null
});


export function Shell({
  tabs
}: {
  tabs: Tab[]
}) {

  const socket = useRef<WebSocket>(null)
  const poller = useRef<ReturnType<typeof setInterval> | undefined>(null)

  useEffect(() => {

    const conn = new WebSocket("ws://" + location.host + "/echo")

    conn.addEventListener("open", (event) => {
      conn.send("connection")
    })

    conn.addEventListener("message", (event) => {
      const msg = JSON.parse(event.data)
      if(msg.status === 'done') {
        notifications.show({
          autoClose: false,
          title: 'Process finished',
          message: null,
          position: 'top-right'
        })
        console.log(msg.output)
        setStatus(status => ({ ...status, loading: false}))
        clearInterval(poller.current)
      }
    })

    socket.current = conn

    return () => socket.current!.close()
  }, [])

  const [status, setStatus] = useState(defaultRunModelProps)
  const [active, setActive] = useState<LinkIdentifier>('parser');
  const [navs, setNavs] = useState<Link[]>(links)
  const [checks, setChecks] = useState<string[]>([])
  const [precheckPassed, setPrecheckPassed] = useState<boolean>(false);
  const [mobileOpened, { toggle: toggleMobile }] = useDisclosure();
  const [desktopOpened, { toggle: toggleDesktop }] = useDisclosure(true);

  useEffect(() => {
    const precheck = async () => {
      await fetch(
        'http://localhost:5000/train/precheck', {
        method: 'GET'
      })
        .then(response => {
          if (response.ok) return response.json()
          throw new Error(`Server response status @ ${response.status}. Check your browser network tab for traceback.`);
        })
        .then(json => {
          if (!json.passed) {
            setNavs(curr =>
              curr.map(lk => {
                if(lk.id == 'train') return ({ ...lk, disabled: true})
                else return lk
              })
            )
            setChecks(json.checks.failed)
            return;
          }
          setPrecheckPassed(true)
        })
        .catch(error => {
          notifications.show({
            title: 'Encountered some errors',
            message: error.message,
          })
        })
      }

      precheck()
  }, [])

  const notice = checks ? (
    <Tooltip
      multiline
      position="right"
      className={classes.notice}
      label={<>
        <div className={classes.noticeSection}>Check your <b>requirements-dev.txt</b> to run models. You need to install the following packages:</div>
        <Divider />
        <div className={classes.noticeSection}>
          <List style={{ padding: 0}}>{checks.map(ck => <List.Item>{ck}</List.Item>)}</List>
        </div>
      </>}
    >
      <Badge className={classes.badge} rightSection={<IconHelp size={12} />}>
        disabled
      </Badge>
    </Tooltip>
  ) : null

  const running = status.loading ? (
    <Loader color="var(--bg-3)" size="sm" ml={10}/>
  ) : null

  const linkables = navs.map((item) => (
    <Anchor
      component='button'
      className={classes.link}
      data-active={item.id === active || undefined}
      key={item.label}
      disabled={item.disabled}
      onClick={(event) => {
        event.preventDefault();
        setActive(item.id);
      }}
    >
      <Flex justify="flex-start">
        <item.icon className={classes.linkIcon} stroke={1.5} />
        <span>{item.label}</span>
      </Flex>
      <Flex>
        {item.disabled && notice}
        {item.id === 'train' && status.loading && running}
      </Flex>
    </Anchor>
  ));

  const componentize = useMemo(() =>
    tabs.find(comp => comp.id === active)!.component || null
  , [active])

   return (
     <RunModelContext.Provider value={{ status, setStatus, poller, socket}}>
     <ShellContext.Provider value={{ links, active, setActive, precheckPassed, setPrecheckPassed}}>
      <AppShell
        header={{ height: 60 }}
        navbar={{
          width: 300,
          breakpoint: 'sm',
          collapsed: { mobile: !mobileOpened, desktop: !desktopOpened },
        }}
        padding={0}
      >
        <AppShell.Header className={classes.appShellHeader}>
          <Group h="100%" px="md">
            <Burger opened={mobileOpened} onClick={toggleMobile} hiddenFrom="sm" size="sm" color="var(--fg)" />
            <Burger opened={desktopOpened} onClick={toggleDesktop} visibleFrom="sm" size="sm" color="var(--fg)" />
            <Group>
              <Logo className={classes.appShellLogo} />
              <Title order={2}>Ingredient Parser</Title>
            </Group>
          </Group>
        </AppShell.Header>
        <AppShell.Navbar p="md" className={classes.appShellNavBar}>
          {linkables}
        </AppShell.Navbar>
        <AppShell.Main>
          {componentize}
        </AppShell.Main>
      </AppShell>
      </ShellContext.Provider>
      </RunModelContext.Provider>
   )
 }
