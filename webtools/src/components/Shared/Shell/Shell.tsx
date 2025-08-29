// {{{EXTERNAL}}}
import {
	ActionIcon,
	Anchor,
	AppShell,
	Flex,
	Group,
	Loader,
	Stack,
	Text,
} from "@mantine/core";
// {{{ASSETS}}}
import {
	IconArrowBarLeft,
	IconArrowBarRight,
	IconExternalLink,
} from "@tabler/icons-react";
import cx from "clsx";
import { Fragment } from "react";
import { useShallow } from "zustand/react/shallow";
import { ReactComponent as Logo } from "../../../assets/logo.svg";
// {{INTERNAL}}
import { useAppShellStore, useTabTrainerStore } from "../../../domain";
import {
	LabellerDefinitionsModal,
	ShellPreCheckListener,
	ShellTrainingCountdownListener,
	ShellWebSocketListener,
	TabCloseListener,
	TabMultipleListener,
	TabTitleListener,
	TooltipExtended,
} from "..";
// {{{STYLES}}}
import { default as classes } from "./Shell.module.css";

export function Shell() {
	const { tabs, links, currentTab, setCurrentTab, openedNav, toggleNav } =
		useAppShellStore(
			useShallow((state) => ({
				tabs: state.tabs,
				links: state.links,
				currentTab: state.currentTab,
				setCurrentTab: state.setCurrentTab,
				openedNav: state.openedNav,
				toggleNav: state.toggleNav,
			})),
		);

	const { training } = useTabTrainerStore(
		useShallow((state) => ({
			training: state.training,
		})),
	);

	const linkables = links.map((item) => {
		const anchor = (
			<Anchor
				key={`linkable-anchor-${item.label}`}
				td="none"
				fw={500}
				component="button"
				className={cx(classes.link, { [classes.linkCollapsed]: !openedNav })}
				data-active={item.id === currentTab.id || undefined}
				disabled={item.disabled}
				onClick={(event) => {
					event.preventDefault();
					const match = tabs.find((tab) => item.id === tab.id);
					if (!match) return;
					setCurrentTab(match);
				}}
			>
				<Flex justify={openedNav ? "flex-start" : "center"}>
					{training && item.id === "train" ? (
						<Loader
							size={25}
							color="var(--fg-3)"
							className={cx(classes.trainingIcon, {
								[classes.linkIconCollapsed]: !openedNav,
							})}
						/>
					) : (
						<item.icon
							className={cx(classes.linkIcon, {
								[classes.linkIconCollapsed]: !openedNav,
							})}
							stroke={1.5}
						/>
					)}
					{openedNav && <span>{item.label}</span>}
				</Flex>
			</Anchor>
		);

		const wrapper = openedNav ? (
			<Fragment key={`wrapper-fragment-${item.label}`}>{anchor}</Fragment>
		) : (
			<TooltipExtended
				key={`wrapper-tooltip-${item.label}`}
				label={item.label}
				position="right"
			>
				{anchor}
			</TooltipExtended>
		);

		return wrapper;
	});

	const componentize =
		tabs.find((comp) => comp.id === currentTab.id)?.component || null;

	return (
		<>
			<ShellWebSocketListener />
			<ShellPreCheckListener />
			<ShellTrainingCountdownListener />

			<TabTitleListener />
			<TabCloseListener />
			<TabMultipleListener />
			<LabellerDefinitionsModal />

			<AppShell
				navbar={{
					width: openedNav ? 300 : 60,
					breakpoint: 0,
				}}
				padding={0}
			>
				<AppShell.Navbar className={classes.appShellNavBar}>
					{openedNav ? (
						<Group justify="space-between">
							<Group mb="md" wrap="nowrap">
								<Logo style={{ width: 50, height: 50 }} />
								<Stack>
									<Text variant="light" lh={1}>
										Ingredient Parser
									</Text>
									<Anchor
										td="none"
										variant="light"
										size="xs"
										mt="calc(-1*var(--xsmall-spacing))"
										lh={1}
										target="_blank"
										href="https://ingredient-parser.readthedocs.io"
									>
										<Group gap={3}>
											<span>View the docs</span>
											<IconExternalLink size={12} />
										</Group>
									</Anchor>
								</Stack>
							</Group>
							<Flex mb="md">
								<ActionIcon
									variant="transparent-light"
									size={24}
									onClick={toggleNav}
								>
									<IconArrowBarLeft size={24} />
								</ActionIcon>
							</Flex>
						</Group>
					) : (
						<Flex mb="md" style={{ height: 50 }}>
							<ActionIcon
								variant="transparent-light"
								size={24}
								onClick={toggleNav}
							>
								<IconArrowBarRight size={24} />
							</ActionIcon>
						</Flex>
					)}
					{linkables}
				</AppShell.Navbar>
				<AppShell.Main>{componentize}</AppShell.Main>
			</AppShell>
		</>
	);
}
