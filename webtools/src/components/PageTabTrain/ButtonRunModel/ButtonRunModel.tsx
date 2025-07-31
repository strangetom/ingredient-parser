// {{{EXTERNAL}}}
import React, { useState } from "react"
import { ActionIcon, Button, Flex, Group, Loader, Menu, MultiSelect, NumberInput, SegmentedControl, Switch, Text, TextInput } from "@mantine/core"
import { useShallow } from "zustand/react/shallow"
// {{{INTERNAL}}}
import { useTabLabellerStore, useTabTrainerStore } from "../../../domain"
// {{{ASSETS}}}
import { IconChevronDown, IconChevronUp } from "@tabler/icons-react"

export function ButtonRunModel() {

  const {
    connected,
    training,
    onSendTrainRun,
    inputTrainer,
    updateInputTrainer
  } = useTabTrainerStore(
    useShallow((state) => ({
      connected: state.connected,
      training: state.training,
      onSendTrainRun: state.onSendTrainRun,
      inputTrainer: state.input,
      updateInputTrainer: state.updateInput
    })),
  )

  const {
    availablePublisherSources,
    fetchingAvailablePublisherSources,
    input,
    updateInputSettings
  } = useTabLabellerStore(
    useShallow((state) => ({
      availablePublisherSources: state.availablePublisherSources,
      fetchingAvailablePublisherSources: state.fetchingAvailablePublisherSources,
      input: state.input,
      updateInputSettings: state.updateInputSettings
    })),
  )

  const [opened, setOpened] = useState(false);

  const model = (
    <SegmentedControl
      value={inputTrainer.model}
      onChange={(value: string) => {
        updateInputTrainer({ model: value })
      }}
      data={[
        { label: 'Parser', value: 'parser' }
      ]}
    />
  )

  const labelSources = fetchingAvailablePublisherSources ?  (
      <Flex style={{ width: "100%" }}>
        <Loader color="var(--fg)" size={16} />
      </Flex>
  ) : (
      <MultiSelect
        data={availablePublisherSources}
        value={input.settings.sources}
        onChange={(values) => {
          if (values.length === 0) return;
          updateInputSettings({ sources: [...values] })
          updateInputTrainer({ sources: [...values] })
        }}
        comboboxProps={{ withinPortal: false, width: 200, position: "top-start"}}
      />
  )

  const split = (
    <div>
      <NumberInput
        value={inputTrainer.split}
        onChange={(value) => {
          if (!value) return;
          updateInputTrainer({ split: parseFloat(value.toString()) })
        }}
        step={0.1}
        min={0.1}
        max={0.9}
      />
      <Text mt={3} c="var(--fg-4)" size="xs">
        Fraction of data to be used for testing
      </Text>
    </div>
  )

  const htmlSwitch = (
      <Switch
        label="HTML results file"
        description="Output a markdown file containing detailed results"
        checked={inputTrainer.html}
        onChange={(event) => {
          updateInputTrainer({ html: event.currentTarget.checked })
        }}
      />
  )

  const confusionSwitch = (
      <Switch
        label="Confusion"
        description="Plot confusion matrix of token labels"
        checked={inputTrainer.confusion}
        onChange={(event) => {
          updateInputTrainer({ confusion: event.currentTarget.checked })
        }}
      />
  )

  const detailedSwitch = (
      <Switch
        label="Detail result file"
        description="Output a file containing detailed results about accuracy"
        checked={inputTrainer.detailed}
        onChange={(event) => {
          updateInputTrainer({ detailed: event.currentTarget.checked })
        }}
      />
  )

  return connected ? (
    <Group wrap="nowrap" gap={0}>
      <Button
        loading={training}
        style={{ width: 150, height: 50, borderTopRightRadius: 0, borderBottomRightRadius: 0 }}
        variant="dark"
        onClick={onSendTrainRun}
      >
          Run model
      </Button>
        <Menu shadow="md" keepMounted={false} position="bottom-end" width={350} closeOnItemClick={false} offset={8} opened={opened} onChange={setOpened} trigger="click">
          <Menu.Target>
            <ActionIcon
              variant="dark"
              style={{ borderTopLeftRadius: 0, borderBottomLeftRadius: 0, borderTop: 'none', borderBottom: 'none',borderRight: 'none' }}
              size={50}
              disabled={training}
            >
              {opened ? <IconChevronUp size={16} /> : <IconChevronDown size={16} />}
            </ActionIcon>
          </Menu.Target>
          <Menu.Dropdown>
            <Menu.Label>Training model</Menu.Label>
            <Menu.Item component="div">
              {model}
            </Menu.Item>
            <Menu.Divider />
            <Menu.Label>Source datasets for training</Menu.Label>
            <Menu.Item component="div">
              {labelSources}
            </Menu.Item>
            <Menu.Label>Split value</Menu.Label>
            <Menu.Item component="div">
                {split}
            </Menu.Item>
            <Menu.Divider />
            <Menu.Item component="div">
              {htmlSwitch}
            </Menu.Item>
            <Menu.Item component="div">
              {detailedSwitch}
            </Menu.Item>
            <Menu.Item component="div">
              {confusionSwitch}
            </Menu.Item>
          </Menu.Dropdown>
        </Menu>
    </Group>
  )  : null
}
