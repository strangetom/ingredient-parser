// {{{EXTERNAL}}}
import { useEffect } from "react";
// {{{INTERNAL}}}
import { useTabTrainerStore } from "../../../domain";

export function ShellWebSocketListener() {
	useEffect(() => {
		const socket = useTabTrainerStore.getState().socket;
		const onReceiveConnect = useTabTrainerStore.getState().onReceiveConnect;
		const onReceiveDisconnect =
			useTabTrainerStore.getState().onReceiveDisconnect;
		const onReceiveStatus = useTabTrainerStore.getState().onReceiveStatus;
		const onReceiveTrainProgress =
			useTabTrainerStore.getState().onReceiveTrainProgress;

		socket.on("connect", onReceiveConnect);
		socket.on("disconnect", onReceiveDisconnect);
		socket.on("status", onReceiveStatus);
		socket.on("trainer", onReceiveTrainProgress);

		return () => {
			socket.off("connect", onReceiveConnect);
			socket.off("disconnect", onReceiveDisconnect);
			socket.off("status", onReceiveStatus);
			socket.off("trainer", onReceiveTrainProgress);
		};
	}, []);

	return null;
}
