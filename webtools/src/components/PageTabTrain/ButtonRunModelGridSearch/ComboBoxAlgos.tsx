// {{{EXTERNAL}}}
import {
	Anchor,
	Checkbox,
	Combobox,
	Group,
	Input,
	Pill,
	PillsInput,
	Text,
	useCombobox,
} from "@mantine/core";
import { useCallback } from "react";
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import {
	type AlgoVariant,
	collectionsAlgorithms,
	useTabTrainerStore,
} from "../../../domain";

export function ComboBoxAlgos() {
	const { algos } = useTabTrainerStore(
		useShallow((state) => ({
			algos: state.inputGridSearch.algos,
		})),
	);

	const combobox = useCombobox({
		onDropdownClose: () => combobox.resetSelectedOption(),
		onDropdownOpen: () => combobox.updateSelectedOptionIndex("active"),
	});

	const handleValueSelect = useCallback(
		(val: string) => {
			const { updateInputGridSearch } = useTabTrainerStore.getState();
			updateInputGridSearch({
				algos: algos.includes(val as AlgoVariant)
					? algos.filter((v) => v !== (val as AlgoVariant))
					: [...algos, val as AlgoVariant],
			});
		},
		[algos],
	);

	const handleValueRemove = useCallback(
		(val: string) => {
			const { updateInputGridSearch } = useTabTrainerStore.getState();
			updateInputGridSearch({
				algos: algos.filter((v) => v !== val),
			});
		},
		[algos],
	);

	const values = algos.map((item) => (
		<Pill
			key={`algorithm-value-${item}`}
			withRemoveButton
			onRemove={() => handleValueRemove(item)}
		>
			{item}
		</Pill>
	));

	const options = collectionsAlgorithms.map((item) => (
		<Combobox.Option
			key={`algorithm-option-${item.value}`}
			py="xs"
			value={item.value}
			active={algos.includes(item.value)}
		>
			<Group gap="sm">
				<Checkbox
					checked={algos.includes(item.value)}
					onChange={() => {}}
					aria-hidden
					tabIndex={-1}
					style={{ pointerEvents: "none" }}
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
		<Combobox
			store={combobox}
			onOptionSubmit={handleValueSelect}
			withinPortal={false}
			width={400}
			position="top-start"
		>
			<Combobox.DropdownTarget>
				<PillsInput pointer onClick={() => combobox.toggleDropdown()}>
					<Pill.Group>
						{values.length > 0 ? (
							values
						) : (
							<Input.Placeholder color="var(--fg)" opacity={0.33}>
								Pick one or more algorithms
							</Input.Placeholder>
						)}

						<Combobox.EventsTarget>
							<PillsInput.Field
								type="hidden"
								onBlur={() => combobox.closeDropdown()}
								onKeyDown={(event) => {
									if (event.key === "Backspace" && algos.length > 0) {
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
				<Combobox.Footer
					style={{
						borderTop:
							"var(--divider-size)  var(--divider-border-style, solid) color-mix(in srgb,var(--fg),transparent 66%);",
					}}
				>
					<Text fz="xs">
						More information on these algorithms can be found on the{" "}
						<Anchor
							target="_blank"
							fz="inherit"
							href="https://www.chokkan.org/software/crfsuite/manual.html"
						>
							research page
						</Anchor>{" "}
						or{" "}
						<Anchor
							target="_blank"
							fz="inherit"
							href="https://github.com/chokkan/crfsuite"
						>
							github
						</Anchor>
					</Text>
				</Combobox.Footer>
			</Combobox.Dropdown>
		</Combobox>
	);
}
