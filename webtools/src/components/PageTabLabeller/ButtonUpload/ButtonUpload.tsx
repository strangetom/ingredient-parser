// {{{EXTERNAL}}}
import {
	Box,
	Button,
	type ButtonProps,
	Drawer,
	type DrawerOverlayProps,
	type DrawerProps,
	Group,
	Stepper,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
// {{{ASSETS}}}
import { IconUpload } from "@tabler/icons-react";
import type React from "react";
import { useEffect } from "react";
import { useShallow } from "zustand/react/shallow";
import {
	TOTAL_UPLOAD_STEPS,
	useTabLabellerStore,
	useUploadNewLabellersStore,
} from "../../../domain";
// {{{EXTERNAL}}}
import { Sectionable } from "../../Shared";
// {{{STYLES}}}
import classes from "./ButtonUpload.module.css";
import { StepOne, StepThree, StepTwo } from "./steps";

function UploadMountListener() {
	useEffect(() => {
		const { setState, resetState, onIngredientSentenceEntryHandler } =
			useUploadNewLabellersStore.getState();

		setState({
			stepCallbackFns: [onIngredientSentenceEntryHandler, null, null],
		});

		return () => {
			resetState();
		};
	}, []);

	return null;
}

interface UploadSheetProps {
	opened: DrawerProps["opened"];
	onClose: DrawerProps["onClose"];
	footer?: React.ReactNode;
	drawerProps?: DrawerProps;
	children?: React.ReactNode;
}

export function UploadSheet({
	footer = null,
	opened,
	onClose,
	children,
	drawerProps,
	...others
}: UploadSheetProps) {
	const defaultDrawerProps = {
		size: "lg",
		position: "bottom",
		transitionProps: {
			transition: "fade-up",
			duration: 150,
			timingFunction: "ease",
		},
		closeOnClickOutside: false,
		keepMounted: false,
		...drawerProps,
	} as Partial<DrawerProps>;

	const defaultOverlayProps = {
		opacity: 1,
		backgroundOpacity: 0.86,
	} as Partial<DrawerOverlayProps>;

	return (
		<Drawer.Root
			opened={opened}
			onClose={onClose}
			trapFocus={false}
			{...defaultDrawerProps}
			{...others}
		>
			<Drawer.Overlay {...defaultOverlayProps} />

			<Drawer.Content className={classes.content}>
				<Box className={classes.inner}>
					{children}
					{footer && (
						<Sectionable.ActionBar position="bottom">
							{footer}
						</Sectionable.ActionBar>
					)}
				</Box>
			</Drawer.Content>
		</Drawer.Root>
	);
}

export function ButtonUpload(props: ButtonProps) {
	const { preuploading } = useTabLabellerStore(
		useShallow((state) => ({
			preuploading: state.preuploading,
		})),
	);

	const {
		bulkUploadApi,
		publisherSource,
		rawText,
		activeStep,
		setState,
		onNextStepHandler,
		onPrevStepHandler,
	} = useUploadNewLabellersStore(
		useShallow((state) => ({
			bulkUploadApi: state.bulkUploadApi,
			publisherSource: state.publisherSource,
			rawText: state.rawText,
			activeStep: state.activeStep,
			setState: state.setState,
			onNextStepHandler: state.onNextStepHandler,
			onPrevStepHandler: state.onPrevStepHandler,
		})),
	);

	const [opened, { open, close }] = useDisclosure(false);

	const onUploadBulkApiHandler = async () => {
		const result = await bulkUploadApi();
		if (result) close();
	};

	const onOpenHandler = () => {
		const {
			hasUnsavedChanges,
			setUnsavedChangesModalOpen,
			setUnsavedChangesFnCallback,
		} = useTabLabellerStore.getState();
		if (hasUnsavedChanges()) {
			setUnsavedChangesFnCallback(open);
			setUnsavedChangesModalOpen(true);
		} else {
			open();
		}
	};

	return (
		<>
			<Button
				variant="dark"
				h={50}
				leftSection={<IconUpload size={16} />}
				onClick={onOpenHandler}
				{...props}
			>
				Upload New
			</Button>

			{opened && <UploadMountListener />}

			<UploadSheet
				footer={
					<Group
						gap="var(--xsmall-spacing)"
						style={{ width: "100%", justifyContent: "flex-end" }}
					>
						<Button variant="dark" onClick={close}>
							Cancel
						</Button>
						{activeStep !== 0 && (
							<Button variant="light" onClick={onPrevStepHandler}>
								Back
							</Button>
						)}
						{activeStep !== TOTAL_UPLOAD_STEPS - 1 && (
							<Button
								variant="light"
								onClick={onNextStepHandler}
								loading={preuploading}
								disabled={rawText.length === 0}
							>
								Next
							</Button>
						)}
						{activeStep === TOTAL_UPLOAD_STEPS - 1 && (
							<Button
								variant="light"
								disabled={!publisherSource}
								onClick={onUploadBulkApiHandler}
							>
								Upload entries
							</Button>
						)}
					</Group>
				}
				opened={opened}
				onClose={close}
			>
				<Stepper
					active={activeStep}
					onStepClick={(stepIndex: number) =>
						setState({ activeStep: stepIndex })
					}
					classNames={{
						steps: classes.stepperSteps,
						root: classes.stepperRoot,
						content: classes.stepperContent,
					}}
					unstyled
				>
					<Stepper.Step>
						<StepOne />
					</Stepper.Step>
					<Stepper.Step>
						<StepTwo />
					</Stepper.Step>
					<Stepper.Completed>
						<StepThree />
					</Stepper.Completed>
				</Stepper>
			</UploadSheet>
		</>
	);
}
