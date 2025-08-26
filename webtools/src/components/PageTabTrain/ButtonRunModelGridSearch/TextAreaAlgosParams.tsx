// {{{EXTERNAL}}}
import {
	Anchor,
	Badge,
	Box,
	Code,
	Combobox,
	Group,
	JsonInput,
	LoadingOverlay,
	Text,
	useCombobox,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import {
	IconArrowLeft,
	IconEye,
	IconSwitchVertical,
	IconX,
} from "@tabler/icons-react";
import {
	createContext,
	forwardRef,
	useContext,
	useMemo,
	useState,
} from "react";
import { useShallow } from "zustand/react/shallow";
import {
	type AlgoVariant,
	type AlgoVariantStoreNamespace,
	safeParseJsonPrettyStringify,
	useTabTrainerStore,
	validateJson,
} from "../../../domain";
import { ActionIconTooltipped } from "../../Shared";
// {{{INTERNAL}}}
import {
	algorithmsNamespaceToVariant,
	algorithmsVariantToNamespace,
} from "./algorithmVariantNamespace";

interface VariantNamespaceType {
	variantNameSpace: AlgoVariantStoreNamespace;
	setVariantNamespace: React.Dispatch<
		React.SetStateAction<AlgoVariantStoreNamespace>
	>;
	jsonError: boolean;
	setJsonError: React.Dispatch<React.SetStateAction<boolean>>;
}

export const AlgoVariantStoreContext = createContext<VariantNamespaceType>({
	variantNameSpace: "algosGlobalParams",
	setVariantNamespace: () => {},
	jsonError: false,
	setJsonError: () => {},
});

const ActionIconTooltippedTarget = forwardRef<
	HTMLDivElement,
	React.ComponentPropsWithoutRef<"div">
>((props, ref) => (
	<div ref={ref} {...props}>
		<ActionIconTooltipped
			text="Switch algorithm"
			iconography={IconSwitchVertical}
		/>
	</div>
));

export function TextAreaComboBoxSwitcher() {
	const { algos } = useTabTrainerStore(
		useShallow((state) => ({
			algos: state.inputGridSearch.algos,
		})),
	);

	const { setJsonError, variantNameSpace, setVariantNamespace } = useContext(
		AlgoVariantStoreContext,
	);

	const combobox = useCombobox({
		onDropdownClose: () => combobox.resetSelectedOption(),
	});

	const options = ["global", ...algos].map((item) => (
		<Combobox.Option
			value={item}
			key={item}
			active={
				item ===
				(algorithmsNamespaceToVariant[
					variantNameSpace
				] as AlgoVariantStoreNamespace)
			}
		>
			<Group gap="xs" style={{ width: "100%" }} justify="space-between">
				<span>{item}</span>
				{item ===
					(algorithmsNamespaceToVariant[
						variantNameSpace
					] as AlgoVariantStoreNamespace) && (
					<IconArrowLeft color="var(--fg)" size={16} />
				)}
			</Group>
		</Combobox.Option>
	));

	return (
		<Combobox
			store={combobox}
			width={150}
			position="top-end"
			withinPortal={false}
			onOptionSubmit={(val: string) => {
				if (!val) return;
				const variantNamespaceResolved = algorithmsVariantToNamespace[
					val as AlgoVariant
				] as AlgoVariantStoreNamespace;
				setVariantNamespace(variantNamespaceResolved);
				const { inputGridSearch } = useTabTrainerStore.getState();
				const optimisticJsonStr = inputGridSearch[variantNamespaceResolved];
				const isValid = validateJson(optimisticJsonStr, JSON.parse);
				if (isValid) {
					setJsonError(false);
				} else {
					setJsonError(true);
				}
				combobox.closeDropdown();
			}}
		>
			<Combobox.Target targetType="button">
				<ActionIconTooltippedTarget onClick={() => combobox.toggleDropdown()} />
			</Combobox.Target>

			<Combobox.Dropdown>
				<Combobox.Options>{options}</Combobox.Options>
			</Combobox.Dropdown>
		</Combobox>
	);
}

function TextAreaParamsDisclaimer() {
	return (
		<Text fz="xs" mt="xs">
			View CRFSuite's{" "}
			<Anchor
				target="_blank"
				fz="inherit"
				href="https://www.chokkan.org/software/crfsuite/manual.html"
			>
				hyper-parameters documentation
			</Anchor>
		</Text>
	);
}

function TextAreaAlgosJson() {
	const { inputGridSearch, updateInputGridSearch } = useTabTrainerStore(
		useShallow((state) => ({
			inputGridSearch: state.inputGridSearch,
			updateInputGridSearch: state.updateInputGridSearch,
		})),
	);

	const { jsonError, setJsonError, variantNameSpace } = useContext(
		AlgoVariantStoreContext,
	);

	const [prettyJsonOpened, { open: openPrettyJson, close: closePrettyJson }] =
		useDisclosure(false);

	const optimisticJsonStr = useMemo(
		() => inputGridSearch[variantNameSpace],
		[variantNameSpace, inputGridSearch],
	);

	return (
		<Box style={{ position: "relative" }}>
			<LoadingOverlay
				visible={prettyJsonOpened}
				loaderProps={{
					style: {
						position: "relative",
						height: "100%",
						width: "100%",
					},
					children: (
						<div
							style={{
								position: "relative",
								height: "100%",
								width: "100%",
							}}
						>
							<Code block style={{ height: "100%", width: "100%" }}>
								{!jsonError &&
									safeParseJsonPrettyStringify(
										optimisticJsonStr,
										JSON.parse,
										JSON.stringify,
									)}
							</Code>
							<Box
								style={{
									position: "absolute",
									top: "var(--xsmall-spacing)",
									right: "var(--xsmall-spacing)",
								}}
							>
								<ActionIconTooltipped
									text="Exit"
									iconography={IconX}
									onClick={closePrettyJson}
								/>
							</Box>
						</div>
					),
				}}
				zIndex={99999}
				overlayProps={{
					blur: 0,
					backgroundOpacity: 0.9,
					color: "var(--bg-1)",
					center: false,
				}}
				styles={{
					root: {
						display: "block",
						align: undefined,
						justifyContent: undefined,
					},
				}}
			/>
			<JsonInput
				value={optimisticJsonStr}
				onChange={(value) => {
					updateInputGridSearch({ [variantNameSpace]: value });
					const isValid = validateJson(value, JSON.parse);
					if (isValid) {
						setJsonError(false);
					} else {
						setJsonError(true);
					}
				}}
				errorProps={{ display: jsonError ? "block" : "none" }}
				validationError="Invalid JSON — parameters will be ignored unless corrected"
				rows={4}
				rightSectionWidth={80}
				rightSection={
					<Box style={{ position: "relative", height: "100%", width: 80 }}>
						<Box
							style={{
								position: "absolute",
								bottom: "var(--xsmall-spacing)",
								right: "var(--xsmall-spacing)",
							}}
						>
							<Group gap={6}>
								<ActionIconTooltipped
									text="Preview pretty format"
									iconography={IconEye}
									onClick={openPrettyJson}
									actionIconProps={{ disabled: jsonError }}
								/>
								<TextAreaComboBoxSwitcher />
							</Group>
						</Box>
						<Box
							style={{
								position: "absolute",
								top: "var(--xsmall-spacing)",
								right: "var(--xsmall-spacing)",
							}}
						>
							<Badge variant="dark" style={{ display: "grid" }}>
								{algorithmsNamespaceToVariant[variantNameSpace]}
							</Badge>
						</Box>
					</Box>
				}
			/>
		</Box>
	);
}

export function TextAreaAlgosParams() {
	const [variantNameSpace, setVariantNamespace] =
		useState<AlgoVariantStoreNamespace>("algosGlobalParams");
	const [jsonError, setJsonError] = useState(false);

	return (
		<AlgoVariantStoreContext.Provider
			value={{ variantNameSpace, setVariantNamespace, jsonError, setJsonError }}
		>
			<TextAreaAlgosJson />
			<TextAreaParamsDisclaimer />
		</AlgoVariantStoreContext.Provider>
	);
}
