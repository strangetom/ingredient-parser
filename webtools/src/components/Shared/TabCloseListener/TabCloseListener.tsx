// {{EXTERNAL}}
import { useCallback, useEffect } from "react";
import { useShallow } from "zustand/react/shallow";
// {{INTERNAL}}
import { useTabTrainerStore } from "../../../domain";

export function TabCloseListener() {
	const { training } = useTabTrainerStore(
		useShallow((state) => ({
			training: state.training,
		})),
	);

	const alertBeforeCloseWhenTraining = useCallback(
		(event: BeforeUnloadEvent) => {
			if (training) event.preventDefault();
		},
		[training],
	);

	useEffect(() => {
		window.addEventListener("beforeunload", alertBeforeCloseWhenTraining);

		return () => {
			window.removeEventListener("beforeunload", alertBeforeCloseWhenTraining);
		};
	}, [alertBeforeCloseWhenTraining]);

	return null;
}
