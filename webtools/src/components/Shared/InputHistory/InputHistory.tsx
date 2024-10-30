// {{{EXTERNAL}}}
import React, { useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { ActionIcon, Box, Center, Flex, Pagination, Text } from '@mantine/core';
import { useHotkeys, useSessionStorage, useShallowEffect } from '@mantine/hooks';
// {{{INTERNAL}}}
import { Input, InputContext } from "../../MainTryParser"
// {{{ASSETS}}}

// {{{STYLES}}}
import { default as classes } from './InputHistory.module.css';
import { ActionIconTooltipped } from '../';
// {{{ASSETS}}}
import { IconChevronLeft, IconChevronRight, IconTrash } from '@tabler/icons-react';


export function InputHistory({
  onCallback
}: {
  onCallback?: (inputProvided: Input) => void
}) {

  const [inputLog, setInputLog] = useSessionStorage<Input[]>({
    key: 'log',
    defaultValue: [],
    getInitialValueInEffect: false
  });

  const [viewingIndex, setViewingIndex] = useState(0)
  const bounds = useMemo(() => ({ lower: 0, upper: inputLog.length - 1 }), [inputLog])


  useShallowEffect(()=> {
    if(bounds) setViewingIndex(0)
  }, [bounds])

  const onClearInputLogHandler = useCallback(() => {
    setInputLog([])
  }, [])

  const onInputClickHandler =  useCallback(() => {
    onCallback?.(inputLog[viewingIndex])
  }, [onCallback, viewingIndex, inputLog])

  const onPrevHandler =  useCallback(() => {
    setViewingIndex(o => (o-1 < bounds.lower) ? o : o-1)
  }, [bounds])

  const onNextHandler =  useCallback(() => {
    setViewingIndex(o => (o+1 > bounds.upper) ? o : o+1)
  }, [bounds])

  /*
  useHotkeys(
    [
      ['ArrowRight', onNextHandler],
      ['ArrowLeft', onPrevHandler],
      ['mod+Enter', onInputClickHandler]
    ],
    ['INPUT', 'TEXTAREA']
  );
 */
   return (
     <Flex>
        <Box className={classes.log}>
          {inputLog[viewingIndex].sentence}
        </Box>
        <div className={classes.left}>
        <ActionIconTooltipped
          iconography={IconChevronLeft}
          text="previous entry in log"
          onClick={onPrevHandler}
        />
        </div>
        <div className={classes.right}>
          <ActionIconTooltipped
            iconography={IconChevronRight}
            text="next entry in log"
            onClick={onNextHandler}
          />
        </div>
        <div className={classes.trash}>
        <ActionIconTooltipped
           actionIconProps={{ color: "red" }}
          iconography={IconTrash}
          text="remove all entries"
          onClick={onClearInputLogHandler}
        />
       </div>
     </Flex>
   )
 }
