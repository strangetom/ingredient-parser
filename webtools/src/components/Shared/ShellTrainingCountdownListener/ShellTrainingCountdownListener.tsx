// {{EXTERNAL}}
import { useEffect } from "react";
// {{INTERNAL}}
import { subscribeCounterStore, useTabTrainerStore } from "../../../domain";

export function ShellTrainingCountdownListener() {
	useEffect(() => {
		const subscriptionTrainingStatusStore = useTabTrainerStore.subscribe(
			(state) => state.training,
			(training) => {
				subscribeCounterStore(training);
			},
		);

		return () => {
			subscriptionTrainingStatusStore();
		};
	}, []);

	return null;
}
