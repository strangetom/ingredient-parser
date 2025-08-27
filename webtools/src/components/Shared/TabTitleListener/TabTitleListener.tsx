// {{EXTERNAL}}

import { useDocumentTitle, useInterval } from "@mantine/hooks";
import { useEffect, useRef, useState } from "react";
import { useShallow } from "zustand/react/shallow";
// {{INTERNAL}}
import {
	toTitleCase,
	useAppShellStore,
	useTabTrainerStore,
} from "../../../domain";

export function TabTitleListener() {
	const { currentTab } = useAppShellStore(
		useShallow((state) => ({
			currentTab: state.currentTab,
		})),
	);

	const { training } = useTabTrainerStore(
		useShallow((state) => ({
			training: state.training,
		})),
	);

	const [dots, setDots] = useState(0);
	const intervalRef = useRef(
		useInterval(() => setDots((d) => (d === 3 ? 0 : d + 1)), 1000),
	);

	useEffect(() => {
		intervalRef.current.start();
		return intervalRef.current.stop;
	}, []);

	useDocumentTitle(
		training
			? `Training ${Array(dots).fill(".").join("")}`
			: toTitleCase(currentTab.id),
	);

	return null;
}
