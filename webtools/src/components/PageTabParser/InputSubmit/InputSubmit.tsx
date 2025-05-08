// {{{EXTERNAL}}}
import React, { useCallback, useState } from "react"
import { ActionIcon, ActionIconGroup, ActionIconProps, Button, Combobox, ComboboxProps, Group, Indicator, Menu, ScrollArea, Switch, TextInput, TextInputProps, Transition, useCombobox } from "@mantine/core"
import { getHotkeyHandler } from "@mantine/hooks";
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { useTabParserStore } from "../../../domain";
// {{{ASSETS}}}
import { IconClipboardList, IconClipboardListFilled, IconFilter, IconFilterFilled, IconTrash, IconX } from "@tabler/icons-react"

function ActionIconClear(props: ActionIconProps){

  const {
    sentence,
    updateInput,
    setParsed
  } = useTabParserStore(
    useShallow((state) => ({
      sentence: state.input.sentence,
      updateInput: state.updateInput,
      setParsed: state.setParsed
    })),
  )

  const onClearHandler = () => {
    updateInput({ sentence: "" })
    setParsed(null)
  }

  return (
    <Transition mounted={sentence.length !== 0}>
      {(styles) =>
        <ActionIcon variant="transparent-light" style={{ width: 36, height: 36, ...styles }} onClick={onClearHandler} {...props}>
          <IconX strokeWidth={1}/>
        </ActionIcon>
      }
    </Transition>
  )
}

function ActionIconFilter(props: ActionIconProps) {

  const {
    input,
    updateInput
  } = useTabParserStore(
    useShallow((state) => ({
      input: state.input,
      updateInput: state.updateInput
    })),
  )

  const [opened, setOpened] = useState(false);

  return (
    <Menu shadow="md" position="top-end" width={350} closeOnItemClick={false} offset={8} opened={opened} onChange={setOpened} trigger="click">
      <Menu.Target>
        <ActionIcon style={{ width: 36, height: 36 }} variant="dark" {...props}>
          {opened ? <IconFilterFilled size={16} /> : <IconFilter size={16} />}
        </ActionIcon>
      </Menu.Target>

      <Menu.Dropdown>
        <Menu.Item component="div">
          <Switch
            defaultChecked
            checked={input.foundation_foods}
            label="Foundation food"
            name="FOUNDATION_FOOD"
            onChange={(event) => updateInput({ foundation_foods: event.target.checked })}
            styles={{ root: { width: "100%" }, labelWrapper: { width: "100%" } }}
          />
        </Menu.Item>
        <Menu.Divider />
        <Menu.Item component="div">
          <Switch
            defaultChecked
            checked={input.discard_isolated_stop_words }
            label="Discard isolated stop words"
            name="discard_isolated_stop_words"
            onChange={(event) => updateInput({ discard_isolated_stop_words: event.target.checked })}
            style={{ width: "100%"}}
          />
        </Menu.Item>
        <Menu.Divider />
        <Menu.Item component="div">
          <Switch
            defaultChecked
            checked={input.expect_name_in_output }
            label="Expect name"
            name="expect_name_in_output"
            onChange={(event) => updateInput({ expect_name_in_output: event.target.checked })}
            style={{ width: "100%"}}
          />
        </Menu.Item>
        <Menu.Divider />
        <Menu.Item component="div">
          <Switch
            defaultChecked
            checked={input.string_units }
            label="String units"
            name="string_units"
            onChange={(event) => updateInput({ string_units: event.target.checked })}
            style={{ width: "100%"}}
          />
        </Menu.Item>
        <Menu.Divider />
        <Menu.Item component="div">
          <Switch
            defaultChecked
            checked={input.imperial_units}
            label="Imperial units"
            name="imperial_units"
            onChange={(event) => updateInput({imperial_units: event.target.checked })}
            style={{ width: "100%"}}
          />
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  )
}

function ActionIconHistory(props: ComboboxProps) {

  const {
    updateInput,
    history,
    clearHistory,
    getParsedApi
  } = useTabParserStore(
    useShallow((state) => ({
      updateInput: state.updateInput,
      history: state.history,
      clearHistory: state.clearHistory,
      getParsedApi: state.getParsedApi
    })),
  )

  const combobox = useCombobox({
    onDropdownClose: () => combobox.resetSelectedOption(),
  });

  const options = history.map((item) => (
    <Combobox.Option value={item.timestamp} key={item.sentence}>
      {item.sentence}
    </Combobox.Option>
  )).reverse();

  return (

    <Combobox
      store={combobox}
      width={250}
      position="top-end"
      onOptionSubmit={useCallback((val: string) => {
        const match = history.find(item => item.timestamp === val)
        if (!match) return;
        updateInput({ sentence: match.sentence })
        getParsedApi({ input: match, shouldAddToHistory: false })
      }, [history])}
      {...props}
    >
      <Combobox.Target>
        <ActionIcon disabled={history.length === 0} style={{ width: 36, height: 36 }} variant="dark" onClick={() => combobox.toggleDropdown()}>
          <Indicator disabled={history.length === 0} offset={2} color="var(--fg)">
          {combobox.dropdownOpened ? <IconClipboardListFilled size={16} /> : <IconClipboardList size={16} />}
          </Indicator>
        </ActionIcon>
      </Combobox.Target>

      <Combobox.Dropdown>
        <Combobox.Options>
          <ScrollArea.Autosize type="scroll" mah={200}>
          {options}
          </ScrollArea.Autosize>
        </Combobox.Options>
        <Combobox.Footer p="xs" style={{ borderTop: "1px solid var(--fg-4)"}}>
          <Button leftSection={<IconTrash size={16} />} onClick={() => { combobox.toggleDropdown(); clearHistory() }} variant="light" size="sm">
            Clear history
          </Button>
        </Combobox.Footer>
      </Combobox.Dropdown>
    </Combobox>

  )
}

export function InputSubmit(props: TextInputProps){

  const {
    sentence,
    updateInput,
    getParsedApi
  } = useTabParserStore(
    useShallow((state) => ({
      sentence: state.input.sentence,
      updateInput: state.updateInput,
      getParsedApi: state.getParsedApi
    })),
  )

  return (
    <TextInput
      styles={{ input: { height: 50 }, root: { height: 50}}}
      placeholder="Ingredient sentence, e.g. 1/2 cup of olives"
      value={sentence}
      onChange={(event) => {
        updateInput({ sentence: event.target.value as string })
      }}
      onKeyDown={getHotkeyHandler([
        ['mod+Enter', () => getParsedApi({ shouldAddToHistory: true })],
        ['Enter', () => getParsedApi({ shouldAddToHistory: true })]
      ])}
      rightSection={
        <Group gap="var(--xxsmall-spacing)" mr="var(--xsmall-spacing)">
          <ActionIconClear />
          <ActionIconGroup>
            <ActionIconFilter />
            <ActionIconHistory />
          </ActionIconGroup>
        </Group>
      }
      rightSectionProps={{ style: {backgroundColor: "var(--bg-2)"} }}
      rightSectionWidth="auto"
      {...props}
    />
  )
}
