import { Anchor, Checkbox, Combobox, Group, Input, Pill, PillsInput, Stack, Text, useCombobox } from '@mantine/core';
import { useCallback, useState } from 'react';
import { useTabTrainerStore } from '../../../domain';
import { useShallow } from 'zustand/react/shallow';

interface Item {
  value: string;
  description: string;
  url: string;
}

const groceries: Item[] = [
  { value: 'lbfgs', description: 'Gradient descent using the L-BFGS method', url: '' },
  {  value: 'ap', description: ' Averaged Perceptron', url: '' },
  { value: 'l2sgd', description: 'Stochastic Gradient Descent with L2 regularization term', url: '' },
  { value: 'pa', description: 'Passive Aggressive', url: '' },
  { value: 'arow', description: 'Adaptive Regularization of Weight Vector', url: '' },
];


export function ComboBoxAlgos() {

  const {
    algos,
    updateInputGridSearch
  } = useTabTrainerStore(
    useShallow((state) => ({
      algos: state.inputGridSearch.algos,
      updateInputGridSearch: state.updateInputGridSearch
    })),
  )

  const combobox = useCombobox({
    onDropdownClose: () => combobox.resetSelectedOption(),
    onDropdownOpen: () => combobox.updateSelectedOptionIndex('active'),
  });

  const handleValueSelect = useCallback((val: string) =>
    updateInputGridSearch({
      algos: algos.includes(val) ? algos.filter((v) => v !== val) : [...algos, val]
    }), [algos]);

  const handleValueRemove = useCallback((val: string) =>
    updateInputGridSearch({
      algos: algos.filter((v) => v !== val)
    }), [algos])

  const values = algos.map((item) => (
    <Pill key={item} withRemoveButton onRemove={() => handleValueRemove(item)}>
      {item}
    </Pill>
  ));

  const options = groceries.map((item) => (
    <Combobox.Option py="xs" value={item.value} key={item.value} active={algos.includes(item.value)}>
      <Group gap="sm">
        <Checkbox
          checked={algos.includes(item.value)}
          onChange={() => {}}
          aria-hidden
          tabIndex={-1}
          style={{ pointerEvents: 'none' }}
        />
        <div>
          <Text fz="sm" fw={500}>
            {item.value}
          </Text>
          <Text fz="xs" opacity={0.6}>
            {item.description}
          </Text>
        </div>
      </Group>
    </Combobox.Option>
  ));

  return (
    <Combobox store={combobox} onOptionSubmit={handleValueSelect} withinPortal={false}>
      <Combobox.DropdownTarget>
        <PillsInput pointer onClick={() => combobox.toggleDropdown()}>
          <Pill.Group>
            {values.length > 0 ? (
              values
            ) : (
              <Input.Placeholder color="var(--fg)" opacity={0.33}>Pick one or more algorithms</Input.Placeholder>
            )}

            <Combobox.EventsTarget>
              <PillsInput.Field
                type="hidden"
                onBlur={() => combobox.closeDropdown()}
                onKeyDown={(event) => {
                  if (event.key === 'Backspace' && algos.length > 0) {
                    event.preventDefault();
                    handleValueRemove(algos[algos.length - 1]);
                  }
                }}
              />
            </Combobox.EventsTarget>
          </Pill.Group>
        </PillsInput>
      </Combobox.DropdownTarget>

      <Combobox.Dropdown>
        <Combobox.Options>{options}</Combobox.Options>
        <Combobox.Footer style={{ borderTop: 'var(--divider-size)  var(--divider-border-style, solid) color-mix(in srgb,var(--fg),transparent 66%);'}}>
          <Text fz="xs">
          More information on these algorithms can be found on the <Anchor target="_blank" fz="inherit" href="https://www.chokkan.org/software/crfsuite/manual.html">research page</Anchor> or <Anchor target="_blank" fz="inherit" href="https://github.com/chokkan/crfsuite">github</Anchor>
          </Text>
        </Combobox.Footer>
      </Combobox.Dropdown>

    </Combobox>
  );
}
