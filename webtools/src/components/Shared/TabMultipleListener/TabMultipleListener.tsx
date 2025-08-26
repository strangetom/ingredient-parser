// {{EXTERNAL}}
import { useCallback, useEffect, useRef, useState } from "react";

export function TabMultipleListener() {
	const channel = useRef(new BroadcastChannel("tab"));
	const [original, setOriginal] = useState(false);

	const broadcastListener = useCallback(
		(msg: MessageEvent) => {
			if (msg.data === "tab-secondary-instance" && !original) {
				alert("Cannot open multiple instances");
			} else {
				setOriginal(true);
			}
		},
		[original],
	);

	useEffect(() => {
		channel.current.postMessage("tab-secondary-instance");

		channel.current.addEventListener("message", broadcastListener);

		return () => {
			channel.current.removeEventListener("message", broadcastListener);
		};
	}, [broadcastListener]);

	return null;
}
