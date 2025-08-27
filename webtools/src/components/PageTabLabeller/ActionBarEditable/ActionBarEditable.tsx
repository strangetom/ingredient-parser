// {{{EXTERNAL}}}
import { Button, Group } from "@mantine/core";
import { IconTags } from "@tabler/icons-react";
import { useShallow } from "zustand/react/shallow";
import { useAppShellStore, useTabLabellerStore } from "../../../domain";

export function ActionBarEditable() {
	const { editing, editLabellerItemsApi } = useTabLabellerStore(
		useShallow((state) => ({
			editing: state.editing,
			editLabellerItemsApi: state.editLabellerItemsApi,
		})),
	);

	const { setLabelDefsModalOpen } = useAppShellStore(
		useShallow((state) => ({
			setLabelDefsModalOpen: state.setLabelDefsModalOpen,
		})),
	);
	const onEditApiHandler = async () => {
		await editLabellerItemsApi();
	};

	return (
		<>
			<div />

			<Group gap="xs">
				<Button
					variant="dark"
					h={50}
					onClick={() => setLabelDefsModalOpen(true)}
					leftSection={<IconTags />}
				>
					Label definitions
				</Button>

				<Button
					variant="light"
					h={50}
					onClick={onEditApiHandler}
					loading={editing}
				>
					Save changes
				</Button>
			</Group>
		</>
	);
}
