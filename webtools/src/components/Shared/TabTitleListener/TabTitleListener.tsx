// {{EXTERNAL}}
import React, { useEffect, useState } from 'react'
import { useDocumentTitle, useInterval } from "@mantine/hooks"
import { useShallow } from 'zustand/react/shallow'
// {{INTERNAL}}
import { useTabTrainerStore } from '../../../domain'


function TitleStub() {
  const [dots, setDots] = useState(0);
  const { start, stop } = useInterval(() => setDots((d) => d === 3 ? 0 : d + 1), 1000);

  useEffect(() => {
    start();
    return stop;
  }, []);

  useDocumentTitle(`Training ${Array(dots).fill('.').join('')}`)

  return null
}

export function TabTitleListener(){

  const {
    training
  } = useTabTrainerStore(
    useShallow((state) => ({
      training: state.training
    })),
  )

  // this pattern ensures the document title is only updated during training
  return training ? <TitleStub /> :null
}
