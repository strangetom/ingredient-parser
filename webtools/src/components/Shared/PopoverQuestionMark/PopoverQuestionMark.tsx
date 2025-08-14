// {{{EXTERNAL}}}
import {
	ActionIcon,
	type ActionIconProps,
	type MantineSize,
	type MantineStyleProps,
	Popover,
	type PopoverProps,
	type StylesApiProps,
	Text,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { IconQuestionMark } from "@tabler/icons-react";

export function PopoverQuestionMark({
	shadow = "sm",
	withArrow = true,
	width = 200,
	position = "top",
	size = "xs",
	variant = "light",
	radius = 100,
	background = "var(--bg-2)",
	children,
	...others
}: PopoverProps & {
	variant?: StylesApiProps<{ props: ActionIconProps }>;
	size?: number | MantineSize;
	radius?: number;
	children?: React.ReactNode;
	background?: MantineStyleProps["bg"];
}) {
	const [opened, { close, open, toggle }] = useDisclosure(false);

	return (
		<Popover
			shadow={shadow}
			withArrow={withArrow}
			position={position}
			width={width}
			opened={opened}
			{...others}
		>
			<Popover.Target>
				<ActionIcon
					onClick={toggle}
					size={size}
					variant={variant}
					onMouseEnter={open}
					onMouseLeave={close}
					style={{ cursor: "help", borderRadius: radius }}
				>
					<IconQuestionMark />
				</ActionIcon>
			</Popover.Target>
			<Popover.Dropdown
				bg={background}
				style={{ pointerEvents: "none", padding: "var(--mantine-spacing-xs)" }}
			>
				<Text variant="light" size="xs">
					{children}
				</Text>
			</Popover.Dropdown>
		</Popover>
	);
}
