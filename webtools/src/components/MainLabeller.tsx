// {{{EXTERNAL}}}
import { Box, Button, ButtonProps, Center, Checkbox, Group, Menu, MenuProps, MultiSelect, Pagination, ScrollArea, Text, Textarea, TextInput, TextInputProps } from "@mantine/core"
import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from "react"
import { getHotkeyHandler, useDisclosure, useElementSize, useListState, UseListStateHandlers, useMergedRef, useSessionStorage } from "@mantine/hooks";
import { notifications } from '@mantine/notifications';
import { List as ListVirtual } from 'react-virtualized';
// {{{EXTERNAL}}}
import { Filler, ActionBar, Scrollable, Labeller,  EditSheet, labellers, LabellerSentence, ScrollableVirtualized, LabellerCategory, Sectionable, Sheet } from "./Shared/";
// {{{ASSETS}}}
import { IconFilter, IconFilterFilled, IconUpload } from "@tabler/icons-react"
// {{{STYLES}}}


const OFFSET_MULTIPLIER = 250;

interface Parsed {
  data: any[],
  offset: number;
  total: number;
}

interface Input {
  sentence: string;
  settings: {
    caseSensitive: boolean;
    wholeWord: boolean;
    sources: string[];
    labels: LabellerCategory[]
  }
}

interface InputContextProps {
  inputs: Input,
  setInputs: React.Dispatch<React.SetStateAction<Input>>,
  onInputSearchHandler: ((inputProvided?: Input, offsetPage?: number) => Promise<void>) | ((event?: React.MouseEvent<HTMLButtonElement>) => void),
  loading: boolean;
}

const defaultInputContext = {
  sentence: "",
  settings: {
    caseSensitive: false,
    wholeWord: false,
    sources: ["nyt"],
    labels: ["COMMENT","NAME","PREP","PUNC","PURPOSE","QTY","SIZE","UNIT", "OTHER"] as LabellerCategory[]
  }
}

export const InputContext = createContext<InputContextProps>({
  inputs: defaultInputContext,
  setInputs: () => undefined,
  onInputSearchHandler: () => undefined,
  loading: false
});

interface ParsedContextProps {
  parsed: Parsed | null;
  parsedSentences: any[];
  setParsed: React.Dispatch<React.SetStateAction<Parsed | null>>;
  setParsedSentencesHandler: UseListStateHandlers<any[]>;
}

const ParsedContext = createContext<ParsedContextProps>({
  parsed: null,
  parsedSentences: [],
  setParsed: () => undefined,
  setParsedSentencesHandler: useListState.prototype
});

interface PaginationContextProps {
  activePage: number;
  setActivePage: React.Dispatch<React.SetStateAction<number>>;
}

const PaginationContext = createContext<PaginationContextProps>({
  activePage: 1,
  setActivePage: () => undefined
});

function Editable() {

  // Context, State, Hooks
  const { parsed, parsedSentences, setParsedSentencesHandler } = useContext(ParsedContext)
  const { activePage } = useContext(PaginationContext)
  const { onInputSearchHandler } = useContext(InputContext)
  if (!parsed || !parsedSentences || parsedSentences.length === 0) return null;
  const [ opened, { open, close }] = useDisclosure(false)
  const [loading, setLoading] = useState(false)
  // Handlers
  const onSubmitHandler = useCallback(async () => {

    setLoading(true);
    const edited = parsedSentences.filter(
      value => value.edited
    ).map(
      ({ edited, removed, ...others }) => ({ ...others })
    )

    const removed = parsedSentences.filter(
      value => value.removed
    ).map(
      ({ edited, removed, ...others }) => ({ ...others })
    )

    await fetch(
      'http://localhost:5000/labeller/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          "edited": edited,
          "removed": removed
        })
    })
      .then(response => {
        if (response.ok) return response.json()
        throw new Error(`Server response status @ ${response.status}. Check your browser network tab for traceback.`);
      })
      .then(json => {
        setLoading(false)
        onInputSearchHandler()
        close()
      })
      .catch(error => {
        setLoading(false)
        notifications.show({
          title: 'Encountered some errors',
          message: error.message,
          position: 'top-right'
        })
      })
  }, [parsedSentences, close])
  // Components
  const footer = (<>
    <Text variant="light">
        Editing page {activePage} of {Math.floor(parsed.total / 250)}
    </Text>
    <Group>
      <Button variant="light" onClick={close} disabled={loading}>Cancel</Button>
      <Button variant="light" onClick={onSubmitHandler} loading={loading}>Save edits</Button>
    </Group>
  </>)

  return (
    <>

      <Button variant="light" onClick={open}>
        Enter edit mode
      </Button>

      <EditSheet
        footer={footer}
        opened={opened}
        onClose={close}
        items={parsedSentences}
        handler={setParsedSentencesHandler}
        keepMounted={false}
      />

    </>
  )
}


function InputSubmit({}: TextInputProps){

  // Context, State
  const { setInputs, onInputSearchHandler } = useContext(InputContext)
  const { setActivePage } = useContext(PaginationContext)
  // Handlers
  const onEnterWrapperHandler = useCallback(() => {
    onInputSearchHandler()
    setActivePage(1)
  }, [onInputSearchHandler, setActivePage])
  return (
    <TextInput
      styles={{ input: { width: "100%", height: 50}, root: { width: "calc(100% - 300px)", height: 50}}}
      placeholder="Keyword to search, e.g. tomato"
      onChange={(event) => {
        setInputs(inputs => ({ ...inputs, sentence: event.target.value }))
      }}
      onKeyDown={getHotkeyHandler([
        ['mod+Enter', () => onEnterWrapperHandler()],
        ['Enter', () => onEnterWrapperHandler()]
      ])}
    />
  )
}

function Search(){

  // Context, State
  const { inputs, onInputSearchHandler, loading } = useContext(InputContext)
  const { setActivePage } = useContext(PaginationContext)
  // Handlers
  const onSearchWrapperHandler = useCallback(() => {
    onInputSearchHandler()
    setActivePage(1)
  }, [onInputSearchHandler, setActivePage])
  return (
    <Button
      variant="dark"
      style={{ width: 150, height: 50}}
      onClick={() => onSearchWrapperHandler()}
      loading={loading}
      disabled={!inputs.sentence}
    >
      Search
    </Button>
  )
}

function Upload(){

  // Context, State, Hooks
  const [ opened, { open, close }] = useDisclosure(false)
  const [submitted, setSubmitted] = useState(false)
  const [value, setValue] = useState('')
  const [error, setError] = useState(false)
  // Handlers
  const [values, handlers] = useListState<never[] | any[]>([]);

  const onBackHandler = useCallback(() => {
    setSubmitted(false)
  }, [])
  const onNextHandler = useCallback(async () => {

      if (!value.trim()) {
        setError(true)
        return;
      }

      const ingredients = value
        .split(/\r?\n/)
        .filter(str => str.trim() !== "")

      await fetch(
        'http://localhost:5000/labeller/preupload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sentences: ingredients
        })
      })
        .then(response => {
          if (response.ok) return response.json()
          throw new Error(`Server response status @ ${response.status}. Check your browser network tab for traceback.`);
        })
        .then(json => {
          handlers.setState(json)
          setSubmitted(true)
        })
        .catch(error => {

        })
  }, [value])
  // Components
  const footer = (<>
    {!submitted &&
    <div>
      <Text variant="light">
          Enter ingredients, plain text, separated by newline
      </Text>
    </div>
    }
    { submitted &&
    <div>
      <Text variant="light">
        Hit upload to save edits for new ingredients
      </Text>
    </div>
    }
    <Group>
      <Button variant="light" onClick={close}>Cancel</Button>
      {!submitted && <Button variant="light" onClick={onNextHandler}>Next</Button>}
      {submitted && <Button variant="light" onClick={onBackHandler}>Back</Button>}
      {submitted && <Button variant="light" onClick={()=> null}>Upload</Button>}
    </Group>
  </>)
  const steps = submitted ? (
    <ScrollableVirtualized
      items={values}
      handler={handlers}
      style={{ flexGrow: 1, height:"100%", width: "100%", position: "relative"}}
    />
  ) : (
    <Sectionable padded grow full>
    <Textarea
      placeholder="Paste ingredients here"
      value={value}
      onChange={(event) => {
        if(event.target.value.trim().length === 0) {
          setError(true)
        } else {
          setError(false)
        }
        setValue(event.target.value)
      }}
      error={(error && <div style={{ position: "absolute", top: "calc(var(--small-spacing)*2)", right: "calc(var(--small-spacing)*2)"}}>"Enter at least one ingredient"</div>) || null}
      wrapperProps={{ style: { height: "100%", width: "100%"}}}
      styles={{
        input: { height: "100%", width: "100%" },
        wrapper: {height: "100%", width: "100%" }
      }}
    />
    </Sectionable>
  )

  return (
    <>
      <Button
        variant="dark"
        style={{ width: 125, height: 50}}
        leftSection={<IconUpload size={16} />}
        onClick={open}
      >
        Upload
      </Button>

      <Sheet
        footer={footer}
        opened={opened}
        onClose={close}
      >
        {steps}
        <ActionBar>{footer}</ActionBar>
      </Sheet>
    </>
  )
}

function Paginator(){

  // State
  const { onInputSearchHandler, loading } = useContext(InputContext)
  const { parsed } = useContext(ParsedContext)
  const { activePage, setActivePage } = useContext(PaginationContext)
  // Handlers
  const onChangePaginatorHandler = useCallback((value: number) => {
    setActivePage(value);
    onInputSearchHandler(undefined, (value - 1)*OFFSET_MULTIPLIER)
  }, [onInputSearchHandler])
  return (
    parsed ? (
      <ActionBar>
        <Editable />
        <Pagination total={Math.ceil(parsed.total / 250)} value={activePage} onChange={onChangePaginatorHandler} disabled={loading}/>
      </ActionBar>
    ) : null
  )
}

function Filters({}: MenuProps) {

  const { inputs, setInputs } = useContext(InputContext)
  const [opened, setOpened] = useState(false);

  const labelFilters = (
    <MultiSelect
      data={labellers}
      value={inputs.settings.labels}
      onChange={(values) => {
        if (values.length === 0) return;
        setInputs(o => ({ ...o, settings: { ...o.settings, labels: [...values] as LabellerCategory[] } }))
      }}
      comboboxProps={{ withinPortal: false, width: 200, position: "top-start"}}
    />
  )

  const labelSources = (
      <MultiSelect
        data={["nyt", "bbc", "allrecipes", "cookstr"]}
        value={inputs.settings.sources}
        onChange={(values) => {
          if (values.length === 0) return;
          setInputs(o => ({ ...o, settings: { ...o.settings, sources: [...values] } }))
        }}
        comboboxProps={{ withinPortal: false, width: 200, position: "top-start"}}
      />
  )

  return (
    <Menu shadow="md" position="top-end" width={350} closeOnItemClick={false} offset={8} opened={opened} onChange={setOpened} trigger="click">
      <Menu.Target>
        <Button style={{ width: 150, height: 50 }} variant="dark" rightSection={opened ? <IconFilterFilled size={16} /> : <IconFilter size={16} />}>Filters</Button>
      </Menu.Target>

      <Menu.Dropdown>
        <Menu.Label>Keyword (options)</Menu.Label>
        <Menu.Item component="div">
          <Checkbox
            defaultChecked
            checked={inputs.settings.wholeWord}
            label="Whole word"
            name="WHOLE_WORD"
            onChange={(event) => setInputs(o => ({ ...o, settings: { ...o.settings, wholeWord: event.currentTarget.checked } }))}
            styles={{ root: { width: "100%" }, labelWrapper: { width: "100%" } }}
          />
        </Menu.Item>
        <Menu.Item component="div">
          <Checkbox
            defaultChecked
            checked={inputs.settings.caseSensitive}
            label="Case sensitve"
            name="CASE_SENSITIVE"
            onChange={(event) => setInputs(o => ({ ...o, settings: { ...o.settings, caseSensitive: event.currentTarget.checked } }))}
            styles={{ root: { width: "100%" }, labelWrapper: { width: "100%" } }}
          />
        </Menu.Item>
        <Menu.Divider />
        <Menu.Label>Labels (to search against)</Menu.Label>
        <Menu.Item component="div">
        {labelFilters}
        </Menu.Item>
        <Menu.Divider />
        <Menu.Label>Sources (to search against)</Menu.Label>
        <Menu.Item component="div">
        {labelSources}
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  )
}

export function MainLabeller() {

  // State
  const [activePage, setActivePage] = useState<number>(1);
  const [inputs, setInputs] = useSessionStorage<Input>({
    key: 'input-labeller',
    defaultValue: defaultInputContext
  });
  const [parsed, setParsed] = useState<Parsed | null>(null)
  const [parsedSentences, setParsedSentencesHandler] = useListState()
  const [loading, setLoading] = useState<boolean>(false)
  // Handlers
  const onInputSearchHandler = useCallback(async (inputProvided?: Input, offsetPage?: number) => {
    const inputToSend = inputProvided || inputs;
    if (inputToSend.sentence) {
      setLoading(true)
      await fetch(
        'http://localhost:5000/labeller/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...inputToSend.settings,
          sentence: inputToSend.sentence,
          offset: offsetPage || 0
        })
      })
        .then(response => {
          if (response.ok) return response.json()
          throw new Error(`Server response status @ ${response.status}. Check your browser network tab for traceback.`);
        })
        .then(json => {
          setLoading(false)
          setParsed(json)
          setParsedSentencesHandler.setState(json.data)
        })
        .catch(error => {
          setLoading(false)
          notifications.show({
            title: 'Encountered some errors',
            message: error.message,
            position: 'top-right'
          })
        })
    }
  }, [inputs])

  return (
    <InputContext.Provider value={{ inputs, setInputs, onInputSearchHandler, loading}}>
      <ParsedContext.Provider value={{ parsed, parsedSentences, setParsed, setParsedSentencesHandler}}>
        <PaginationContext.Provider value={{ activePage, setActivePage}}>
          <Box
            style={{
              position: "relative",
              width: "100%",
              height: "100%",
              display: "flex",
              flexDirection: "column"
            }}
          >

            <Sectionable grow>
            {
              parsed &&
              <ScrollableVirtualized
                items={parsed.data}
                style={{ height: "100%", width: "100%"}}
                labellerSentenceProps={{
                  tasks: ["copy"],
                  listable: true
                }}
              />
            }
            {
              !parsed &&
              <Filler text="Search, upload, and edit ingredient labels" illustration="sandwich" />
            }
            </Sectionable>

            {
              parsed &&
              parsedSentences.length !== 0 &&
              <Paginator />
            }

            <ActionBar>
              <InputSubmit />
              <Group gap="var(--small-spacing)" wrap="nowrap" style={{ width: 425}}>
                <Upload />
                <Filters />
                <Search />
              </Group>
            </ActionBar>

          </Box>
        </PaginationContext.Provider>
      </ParsedContext.Provider>
    </InputContext.Provider>
  )
}
