// {{{EXTERNAL}}}
import React, { createContext, useCallback, useContext, useState } from "react"
import { Badge, Box, Button, ButtonProps, Center, Flex, Group, Menu, MenuProps, ScrollArea, Switch, Table, Text, TextInput, TextInputProps, UnstyledButton } from "@mantine/core"
import { getHotkeyHandler, useSessionStorage } from "@mantine/hooks";
import { notifications } from '@mantine/notifications';
// {{{INTERNAL}}}
import { Labeller, LabellerSentence, Token, Confidence, Filler, ActionBar, Scrollable, Sectionable, InputHistory } from "./Shared";
// {{{ASSETS}}}
import { IconChevronDown, IconChevronUp, IconLayoutList, IconLayoutListFilled } from "@tabler/icons-react"

export interface Parsed {
  amounts: Amount[],
  foundation_foods: Confidence[],
  comment: Comment
  name: Confidence
  preparation: Confidence
  purpose: Confidence
  size: Confidence
  tokens: Token[]
}

export interface Amount {
  APPROXIMATE: boolean
  MULTIPLIER: boolean
  RANGE: boolean
  SINGULAR: boolean
  confidence: number
  quantity: number
  quantity_max: number
  starting_index: number
  text: string
  unit: string
}

export interface Input {
  sentence: string;
  discard_isolated_stop_words: boolean;
  expect_name_in_output: boolean;
  string_units: boolean;
  imperial_units: boolean;
  foundation_foods: boolean;
}

interface InputContextProps {
  inputs: Input,
  setInputs: React.Dispatch<React.SetStateAction<Input>>,
  onInputSubmitHandler: ((inputProvided?: Input) => Promise<void>) | ((event?: React.MouseEvent<HTMLButtonElement>) => void),
  loading: boolean;
}

const defaultInputContext = {
  sentence: "",
  discard_isolated_stop_words: true,
  expect_name_in_output: true,
  string_units: false,
  imperial_units: false,
  foundation_foods: false
}

export const InputContext = createContext<InputContextProps>({
  inputs: defaultInputContext,
  setInputs: () => undefined,
  onInputSubmitHandler: () => undefined,
  loading: false
});

interface ParsedContextProps {
  parsed: Parsed | null;
  setParsed: React.Dispatch<React.SetStateAction<Parsed | null>>;
}

export const ParsedContext = createContext<ParsedContextProps>({
  parsed: null,
  setParsed: () => undefined
});

function InputSubmit(props: TextInputProps){

  const { setInputs, onInputSubmitHandler } = useContext(InputContext)

  return (
    <TextInput
      styles={{ input: { width: "100%", height: 50 }, root: { width: "calc(100% - 300px)", height: 50}}}
      placeholder="Ingredient sentence, e.g. 1/2 cup of olives"
      onChange={(event) => setInputs(inputs => ({ ...inputs, sentence: event.target.value }))}
      onKeyDown={getHotkeyHandler([
        ['mod+Enter', () => onInputSubmitHandler()],
        ['Enter', () => onInputSubmitHandler()]
      ])}
    />
  )
}

function Submit(props: ButtonProps){

  const { inputs, onInputSubmitHandler, loading } = useContext(InputContext)

  return (
    <Button
      variant="dark"
      style={{ width: 100, height: 50}}
      onClick={() => onInputSubmitHandler()}
      disabled={!inputs.sentence}
      loading={loading}
    >
      Submit
    </Button>
  )
}

function Options(props: MenuProps) {

  const { inputs, setInputs } = useContext(InputContext)
  const [opened, setOpened] = useState(false);

  return (
    <Menu shadow="md" position="top-end" width={350} closeOnItemClick={false} offset={8} opened={opened} onChange={setOpened} trigger="click">
      <Menu.Target>
        <Button style={{ width: 200, height: 50 }} variant="dark" rightSection={opened ? <IconLayoutListFilled size={16} /> : <IconLayoutList size={16} />}>Options</Button>
      </Menu.Target>

      <Menu.Dropdown>
        <Menu.Item component="div">
          <Switch
            defaultChecked
            checked={inputs.foundation_foods}
            label="Foundation food"
            name="FOUNDATION_FOOD"
            onChange={(event) => setInputs(o => ({ ...o, foundation_foods: event.target.checked }))}
            styles={{ root: { width: "100%" }, labelWrapper: { width: "100%" } }}
          />
        </Menu.Item>
        <Menu.Divider />
        <Menu.Item component="div">
          <Switch
            defaultChecked
            checked={inputs.discard_isolated_stop_words }
            label="Discard isolated stop words"
            name="discard_isolated_stop_words"
            onChange={(event) => setInputs(o => ({ ...o, discard_isolated_stop_words: event.target.checked }))}
            style={{ width: "100%"}}
          />
        </Menu.Item>
        <Menu.Divider />
        <Menu.Item component="div">
          <Switch
            defaultChecked
            checked={inputs.expect_name_in_output }
            label="Expect name"
            name="expect_name_in_output"
            onChange={(event) => setInputs(o => ({ ...o, expect_name_in_output: event.target.checked }))}
            style={{ width: "100%"}}
          />
        </Menu.Item>
        <Menu.Divider />
        <Menu.Item component="div">
          <Switch
            defaultChecked
            checked={inputs.string_units }
            label="String units"
            name="string_units"
            onChange={(event) => setInputs(o => ({ ...o, string_units: event.target.checked }))}
            style={{ width: "100%"}}
          />
        </Menu.Item>
        <Menu.Divider />
        <Menu.Item component="div">
          <Switch
            defaultChecked
            checked={inputs.imperial_units}
            label="Imperial units"
            name="imperial_units"
            onChange={(event) => setInputs(o => ({ ...o, imperial_units: event.target.checked }))}
            style={{ width: "100%"}}
          />
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  )
}

function Results(){

  const { parsed } = useContext(ParsedContext)

  if(!parsed) return null

  const { tokens, amounts, foundation_foods, ...others } = parsed;

  const rows = Object.keys(others).map((k, i) => (
    <Table.Tr key={parsed[k]}>
      <Table.Td width={100} fw="bold">{k.toUpperCase()}</Table.Td>
        <Table.Td>
          {parsed[k].text}
          {parsed[k].confidence !== 0 && <Badge ml={6} variant={k.toUpperCase()}>{(parsed[k].confidence * 100).toFixed(2)}%</Badge>}
      </Table.Td>
    </Table.Tr>
  ));

  const amountsRow = amounts ?  (
    <Table.Tr>
      <Table.Td width={100} fw="bold">AMOUNTS</Table.Td>
        <Table.Td>
        {amounts.map((amount, i) =>
          <span style={{ marginLeft: i === 0 ? 0 : 12 }}>
            {amount.text}
            {amount.confidence !== 0 && <Badge ml={6} variant="AMOUNTS">{(amount.confidence * 100).toFixed(2)}%</Badge>}
          </span>
        )}
      </Table.Td>
    </Table.Tr>
  ) : null

  const foundationFoodsRow = foundation_foods ?  (
    <Table.Tr>
      <Table.Td width={100} fw="bold">FOUNDATION FOODS</Table.Td>
        <Table.Td>
        {foundation_foods.map((foundation_food, i) =>
          <span style={{ marginLeft: i === 0 ? 0 : 12 }}>
            {foundation_food.text}
            {foundation_food.confidence !== 0 && <Badge ml={6} variant="FOUNDATION_FOODS">{(foundation_food.confidence * 100).toFixed(2)}%</Badge>}
          </span>
        )}
      </Table.Td>
    </Table.Tr>
  ) : null

  return (
    <Table>
      <Table.Tbody>
        {amountsRow}
        {foundationFoodsRow}
        {rows}
      </Table.Tbody>
    </Table>
  )
}

export function MainTryParser() {

  const [inputLog, setInputLog] = useSessionStorage<Input[]>({
    key: 'log',
    defaultValue: [],
    getInitialValueInEffect: false
  });
  const [inputs, setInputs] = useSessionStorage<Input>({
    key: 'input-parser',
    defaultValue: defaultInputContext,
    getInitialValueInEffect: false
  });
  const [parsed, setParsed] = useState<Parsed | null>(null)
  const [loading, setLoading] = useState<boolean>(false)

  const onInputSubmitHandler = useCallback(async (inputProvided?: Input) => {
    const inputToSend = inputProvided || inputs;
    if (inputToSend.sentence) {
      setLoading(true)
      await fetch(
        'http://localhost:5000/parser', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...inputToSend
        })
      })
        .then(response => {
          if (response.ok) return response.json()
          throw new Error(`Server response status @ ${response.status}. Check your browser network tab for traceback.`);
        })
        .then(json => {
          setLoading(false)
          setParsed(json);
          if(!inputProvided) setInputLog(inputLog => [inputs, ...inputLog])
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
    <InputContext.Provider value={{ inputs, setInputs, onInputSubmitHandler, loading}}>
      <ParsedContext.Provider value={{ parsed, setParsed}}>
        <Box
          style={{
            position: "relative",
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column"
          }}
        >

          {
            parsed &&
            <Sectionable padded bordered border="bottom">
              <LabellerSentence
                sentence={inputs.sentence}
                tokens={parsed.tokens}
                labellerProps={{ marginalsMode: true, size: "large" }}
              />
            </Sectionable>
          }

          <Sectionable grow padded>
            {parsed && <Results />}
            {!parsed && <Filler text="Enter ingredient sentences" illustration="bowl" />}
          </Sectionable>

          {
            inputLog.length !== 0 &&
            <Sectionable bordered border="top">
            <InputHistory onCallback={onInputSubmitHandler} />
            </Sectionable>
          }

            <ActionBar>
              <InputSubmit />
              <Group gap="xs" wrap="nowrap" style={{ width: 300}}>
                <Options />
                <Submit />
              </Group>
            </ActionBar>

    </Box>
    </ParsedContext.Provider>
    </InputContext.Provider>
  )
}
