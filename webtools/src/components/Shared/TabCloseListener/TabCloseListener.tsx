// {{EXTERNAL}}
import React, { useCallback, useEffect, useRef } from 'react'
import { useDocumentTitle, useInterval } from "@mantine/hooks"
import { useShallow } from 'zustand/react/shallow'
// {{INTERNAL}}
import { useTabTrainerStore } from '../../../domain'

export function TabCloseListener(){

  const {
    training
  } = useTabTrainerStore(
    useShallow((state) => ({
      training: state.training
    })),
  )

  const alertBeforeCloseWhenTraining = useCallback((event: BeforeUnloadEvent) => {
    if(training) {
      event.preventDefault()
      event.returnValue = 'Are you sure you want to exit? You currently are training a model, and it has not completed.'
    }
  }, [training])

  useEffect(() => {

    window.addEventListener("beforeunload", alertBeforeCloseWhenTraining);

    return () => {
      window.removeEventListener("beforeunload", alertBeforeCloseWhenTraining)
    }
  }, [alertBeforeCloseWhenTraining])

  return null
}
