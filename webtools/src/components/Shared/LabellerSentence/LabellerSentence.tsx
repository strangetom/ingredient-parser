// {{{EXTERNAL}}}
import React, { useCallback, useState } from "react"
import { ActionIcon, Badge, Box, Checkbox, CopyButton, ScrollArea, ScrollAreaProps, Tooltip, TooltipProps, ActionIconProps, BoxProps } from "@mantine/core"
import { UseListStateHandlers} from "@mantine/hooks"
import cx from 'clsx';
// {{{INTERNAL}}}
import { Labeller, LabellerProps, Token, ActionIconTooltipped } from "../";
// {{{STYLES}}}
import { default as classes } from "./LabellerSentence.module.css"
import { Icon, IconCheck, IconCopy, IconCopyCheck, IconDots, IconProps, IconTrash, IconTrashFilled, IconTrashXFilled } from "@tabler/icons-react";

export const tsk = ["copy", "remove"] as const;
export type Task = typeof tsk[number];

export interface LabellerSentenceProps extends BoxProps {
  identifier?: number | string;
  tasks?: Task[];
  listable?: boolean;
  labellerProps?: LabellerProps;
  tokens: Token[];
  handler?: UseListStateHandlers<any>,
  sentence: string;
  index?: number;
}

export function LabellerSentence({
  identifier,
  tasks = [],
  listable,
  tokens = [],
  sentence,
  handler,
  labellerProps,
  ...others
}: LabellerSentenceProps) {

  const [selected, setSelected] = useState(false)

  const onSetForRemovalHandler = useCallback(()=>{
    setSelected(o=>!o)
    if(handler) {
      handler.applyWhere(
        (item) => item.id === identifier,
        (item) => ({ ...item, removed: true  })
      );
    }
  },[handler, identifier])

  const onRevertRemovalHandler = useCallback(()=>{
    setSelected(o=>!o)
    if(handler) {
      handler.applyWhere(
        (item) => item.id === identifier,
        (item) => {
          const { removed, ...others } = item
          return ({ ...others })
        }
      );
    }
  },[handler])

  const labellers = tokens.map((tkn, i) =>
    <Labeller {...labellerProps} key={"token-" + i} token={tkn} handler={handler} identifier={identifier}/>
  )

  const scrollable = (
    <Box
      className={classes.sentence}
    >
      {labellers}
    </Box>
  )

  const wrapper = (tasks) ? (
    <Box
      {...others}
      className={cx({
          [classes.listable]: listable
        })
      }
    >
      <Box
        data-selected={selected || undefined}
        className={cx(
          classes.root,
          {
            [classes.spacerLeft]: tasks.length !== 0,
            [classes.spacerRight]: tasks.length !== 0
          })
        }
      >
        <Box className={classes.identifable}>
          {identifier}
        </Box>
        {scrollable}
        <Box className={classes.editable}>
          {
            tasks.includes('copy') &&
            <CopyButton value={sentence}>
              {({ copied, copy }) => (
                copied ? (
                  <ActionIconTooltipped iconography={IconCopyCheck} text="copied" />
                ): (
                  <ActionIconTooltipped iconography={IconCopy} text="copy sentence" onClick={copy} />
                )
              )}
            </CopyButton>
          }
          {
            tasks.includes('remove') && (
              selected ? (
                <ActionIconTooltipped iconography={IconTrashXFilled} onClick={onRevertRemovalHandler} text="undo removal" actionIconProps={{ color: "red"}} />
              ) : (
                <ActionIconTooltipped iconography={IconTrash} onClick={onSetForRemovalHandler} text="mark for removal" actionIconProps={{ color: "red"}} />
              )
            )
          }
        </Box>
      </Box>
    </Box>
  ) : scrollable

  return (
    wrapper
  )
}
