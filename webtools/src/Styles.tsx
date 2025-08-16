// {{{EXTERNAL}}}
import {
	Accordion,
	ActionIcon,
	Affix,
	Anchor,
	AppShell,
	Avatar,
	Badge,
	Button,
	Center,
	Checkbox,
	Code,
	Combobox,
	Container,
	createTheme,
	Dialog,
	Divider,
	Drawer,
	Flex,
	Grid,
	Group,
	Image,
	Indicator,
	Input,
	Kbd,
	List,
	Loader,
	MantineProvider,
	type MantineThemeComponents,
	Menu,
	Modal,
	ModalRoot,
	MultiSelect,
	Notification,
	NumberInput,
	Overlay,
	Pagination,
	Paper,
	Pill,
	Popover,
	Progress,
	Radio,
	RadioIndicator,
	ScrollArea,
	SegmentedControl,
	Select,
	SimpleGrid,
	Skeleton,
	Slider,
	Spoiler,
	Stack,
	Switch,
	Table,
	Text,
	Title,
	Tooltip,
	UnstyledButton,
} from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import { default as accordionClasses } from "./styles/mantine/Accordion.module.css";
import { default as actionIconClasses } from "./styles/mantine/ActionIcon.module.css";
import { default as affixClasses } from "./styles/mantine/Affix.module.css";
import { default as anchorClasses } from "./styles/mantine/Anchor.module.css";
import { default as appShellClasses } from "./styles/mantine/AppShell.module.css";
import { default as avatarClasses } from "./styles/mantine/Avatar.module.css";
import { default as badgeClasses } from "./styles/mantine/Badge.module.css";
import { default as buttonClasses } from "./styles/mantine/Button.module.css";
import { default as checkBoxClasses } from "./styles/mantine/Checkbox.module.css";
import { default as codeClasses } from "./styles/mantine/Code.module.css";
import { default as comboboxClasses } from "./styles/mantine/Combobox.module.css";
import { default as containerClasses } from "./styles/mantine/Container.module.css";
import { default as dividerClasses } from "./styles/mantine/Divider.module.css";
import { default as drawerClasses } from "./styles/mantine/Drawer.module.css";
import { default as flexClasses } from "./styles/mantine/Flex.module.css";
import { default as indicatorClasses } from "./styles/mantine/Indicator.module.css";
import { default as inputClasses } from "./styles/mantine/Input.module.css";
import { default as kbdClasses } from "./styles/mantine/Kbd.module.css";
import { default as listClasses } from "./styles/mantine/List.module.css";
import { default as menuClasses } from "./styles/mantine/Menu.module.css";
import { default as modalClasses } from "./styles/mantine/Modal.module.css";
import { default as multiSelectClasses } from "./styles/mantine/MultiSelect.module.css";
import { default as notificationClasses } from "./styles/mantine/Notification.module.css";
import { default as notificationsClasses } from "./styles/mantine/Notifications.module.css";
import { default as numberInputClasses } from "./styles/mantine/NumberInput.module.css";
import { default as paginationClasses } from "./styles/mantine/Pagination.module.css";
import { default as pillClasses } from "./styles/mantine/Pill.module.css";
import { default as popoverClasses } from "./styles/mantine/Popover.module.css";
import { default as radioClasses } from "./styles/mantine/Radio.module.css";
import { default as radioIndicatorClasses } from "./styles/mantine/RadioIndicator.module.css";
import { default as scrollAreaClasses } from "./styles/mantine/ScrollArea.module.css";
import { default as segmentedControlClasses } from "./styles/mantine/SegmentedControl.module.css";
import { default as selectClasses } from "./styles/mantine/Select.module.css";
import { default as skeletonClasses } from "./styles/mantine/Skeleton.module.css";
import { default as sliderClasses } from "./styles/mantine/Slider.module.css";
import { default as spoilerClasses } from "./styles/mantine/Spoiler.module.css";
import { default as switchClasses } from "./styles/mantine/Switch.module.css";
import { default as tableClasses } from "./styles/mantine/Table.module.css";
import { default as textClasses } from "./styles/mantine/Text.module.css";
import { default as titleClasses } from "./styles/mantine/Title.module.css";
import { default as toolTipClasses } from "./styles/mantine/Tooltip.module.css";
// {{{ INTERNAL }}}
import { default as unstyledButtonClasses } from "./styles/mantine/UnstyledButton.module.css";

export function GlobalStyles({ children }: { children: React.ReactNode }) {
	// Styles
	const components = {
		Loader: Loader.extend({}),
		Pill: Pill.extend({
			classNames: pillClasses,
		}),
		NumberInput: NumberInput.extend({
			classNames: numberInputClasses,
		}),
		Table: Table.extend({
			classNames: tableClasses,
		}),
		Popover: Popover.extend({
			classNames: popoverClasses,
		}),
		Drawer: Drawer.extend({
			classNames: drawerClasses,
		}),
		Indicator: Indicator.extend({
			classNames: indicatorClasses,
		}),
		Spoiler: Spoiler.extend({
			classNames: spoilerClasses,
		}),
		ActionIcon: ActionIcon.extend({
			classNames: actionIconClasses,
		}),
		Badge: Badge.extend({
			classNames: badgeClasses,
		}),
		Slider: Slider.extend({
			classNames: sliderClasses,
		}),
		ScrollArea: ScrollArea.extend({
			classNames: scrollAreaClasses,
		}),
		Input: Input.extend({
			classNames: inputClasses,
		}),
		Accordion: Accordion.extend({
			classNames: accordionClasses,
		}),
		Code: Code.extend({
			classNames: codeClasses,
		}),
		Container: Container.extend({
			classNames: containerClasses,
		}),
		Divider: Divider.extend({
			classNames: dividerClasses,
		}),
		Combobox: Combobox.extend({
			classNames: comboboxClasses,
		}),
		Pagination: Pagination.extend({
			classNames: paginationClasses,
		}),
		Affix: Affix.extend({
			classNames: affixClasses,
		}),
		Checkbox: Checkbox.extend({
			classNames: checkBoxClasses,
		}),
		Radio: Radio.extend({
			classNames: radioClasses,
		}),
		RadioIndicator: RadioIndicator.extend({
			classNames: radioIndicatorClasses,
		}),
		Anchor: Anchor.extend({
			classNames: anchorClasses,
		}),
		Switch: Switch.extend({
			classNames: switchClasses,
		}),
		List: List.extend({
			classNames: listClasses,
		}),
		Avatar: Avatar.extend({
			classNames: avatarClasses,
		}),
		SimpleGrid: SimpleGrid.extend({}),
		Paper: Paper.extend({}),
		Stack: Stack.extend({}),
		Group: Group.extend({}),
		Notification: Notification.extend({
			classNames: notificationClasses,
		}),
		Notifications: Notifications.extend({
			classNames: notificationsClasses,
		}),
		Flex: Flex.extend({
			defaultProps: {
				gap: 0,
				wrap: "nowrap",
				direction: "row",
				justify: "center",
				align: "center",
			},
			classNames: flexClasses,
		}),
		Text: Text.extend({
			classNames: textClasses,
		}),
		Skeleton: Skeleton.extend({
			classNames: skeletonClasses,
		}),
		AppShell: AppShell.extend({
			classNames: appShellClasses,
		}),
		Title: Title.extend({
			classNames: titleClasses,
		}),
		Overlay: Overlay.extend({}),
		Progress: Progress.extend({}),
		Dialog: Dialog.extend({}),
		ModalRoot: ModalRoot.extend({}),
		Modal: Modal.extend({
			classNames: modalClasses,
		}),
		Image: Image.extend({}),
		Center: Center.extend({}),
		Button: Button.extend({
			defaultProps: {
				loaderProps: {
					color: "var(--bg-3)",
				},
			},
			classNames: buttonClasses,
		}),
		UnstyledButton: UnstyledButton.extend({
			classNames: unstyledButtonClasses,
		}),
		Grid: Grid.extend({}),
		Menu: Menu.extend({
			classNames: menuClasses,
		}),
		Tooltip: Tooltip.extend({
			defaultProps: {
				withArrow: true,
				events: {
					hover: true,
					focus: true,
					touch: true,
				},
				multiline: true,
			},
			classNames: toolTipClasses,
		}),
		Kbd: Kbd.extend({
			classNames: kbdClasses,
		}),
		Select: Select.extend({
			classNames: selectClasses,
		}),
		MultiSelect: MultiSelect.extend({
			classNames: multiSelectClasses,
		}),
		SegmentedControl: SegmentedControl.extend({
			classNames: segmentedControlClasses,
		}),
	} as MantineThemeComponents;

	const theme = createTheme({
		scale: 1,
		components: components,
	});

	return (
		<MantineProvider theme={theme}>
			<Notifications />
			{children}
		</MantineProvider>
	);
}
