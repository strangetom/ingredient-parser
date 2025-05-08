// {{{EXTERNAL}}}
import { useEffect } from "react"
import { useShallow } from "zustand/react/shallow"
// {{{INTERNAL}}}
import { useTabTrainerStore } from "../../../domain"

export function ShellWebSocketListener() {

  const {
    socket,
    onReceiveConnect,
    onReceiveDisconnect,
    onReceiveTrainProgress,
    onReceiveStatus
  } = useTabTrainerStore(
    useShallow((state) => ({
      socket: state.socket,
      onReceiveTrainProgress: state.onReceiveTrainProgress,
      onReceiveConnect: state.onReceiveConnect,
      onReceiveDisconnect: state.onReceiveDisconnect,
      onReceiveStatus: state.onReceiveStatus
    })),
  )

  useEffect(() => {

    socket.on('connect', onReceiveConnect);
    socket.on('disconnect', onReceiveDisconnect);
    socket.on('status', onReceiveStatus);
    socket.on('trainer', onReceiveTrainProgress);

    return () => {
      socket.off('connect', onReceiveConnect);
      socket.off('disconnect', onReceiveDisconnect);
      socket.off('status', onReceiveStatus);
      socket.off('trainer', onReceiveTrainProgress);
    };
  }, []);

  return null
}
