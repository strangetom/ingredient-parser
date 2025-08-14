// {{{EXTERNAL}}}

import { Box, Button, Group, Modal, Switch } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import type React from "react";
import { useCallback } from "react";
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { useTabLabellerStore } from "../../../domain";

export function SwitchEditMode() {
	const {
		loading,
		editing,
		editModeEnabled,
		setEditModeEnabled,
		parsedSentences,
	} = useTabLabellerStore(
		useShallow((state) => ({
			loading: state.loading,
			editing: state.editing,
			editModeEnabled: state.editModeEnabled,
			setEditModeEnabled: state.setEditModeEnabled,
			parsedSentences: state.parsedSentences,
		})),
	);

	const [openedDialog, { open: openDialog, close: closeDialog }] =
		useDisclosure(false);

	const onChangeHandler = useCallback(
		(event: React.ChangeEvent<HTMLInputElement>) => {
			const setEditModeEnabled =
				useTabLabellerStore.getState().setEditModeEnabled;
			const hasEdited =
				parsedSentences.filter(({ edited, removed }) => edited || removed)
					.length !== 0;
			if (hasEdited && !event.currentTarget.checked) {
				openDialog();
			} else {
				setEditModeEnabled(event.currentTarget.checked);
			}
		},
		[parsedSentences, openDialog],
	);

	const onOkToProceedHandler = () => {
		closeDialog();
		setEditModeEnabled(false);
	};

	return (
		<>
			<Modal opened={openedDialog} onClose={closeDialog} title="Are you sure?">
				<Box mt="md">
					You have already edited some entries, and they will not be saved until
					you save changes.
				</Box>
				<Group mt="md" justify="flex-end">
					<Button onClick={closeDialog} variant="dark">
						Cancel
					</Button>
					<Button onClick={onOkToProceedHandler} variant="light">
						Yes, I'm sure
					</Button>
				</Group>
			</Modal>

			<Switch
				label="Enable editing"
				checked={editModeEnabled}
				onChange={onChangeHandler}
				disabled={loading || editing}
			/>
		</>
	);
}
