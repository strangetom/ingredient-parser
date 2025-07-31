// {{EXTERNAL}}
import React, { useCallback, useEffect, useState } from 'react'


export function TabMultipleListener() {

  const channel = new BroadcastChannel('tab');
  const [original, setOriginal] = useState(false)

  const broadcastListener = useCallback((msg:  MessageEvent<any>) => {
    if (msg.data === 'tab-secondary-instance' && !original) {
      alert('Cannot open multiple instances');
    }
    else {
      setOriginal(true)
    }
  }, [original])

  useEffect(() => {

    channel.postMessage('tab-secondary-instance');

    channel.addEventListener('message', broadcastListener);

    return () => {
      channel.removeEventListener('message', broadcastListener)
    }

  }, [broadcastListener])

  return null
}
