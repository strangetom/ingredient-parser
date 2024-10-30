// {{{EXTERNAL}}}
import React, { useCallback, useState } from "react"
import { Badge, Box, BoxProps, Flex, Menu, Tooltip, TooltipProps } from "@mantine/core"
import cx from 'clsx';
// {{{ASSETS}}}
import { IconSelector } from "@tabler/icons-react"
// {{{STYLES}}}
import { default as classes } from "./Labeller.module.css"
import { UseListStateHandlers } from "@mantine/hooks";

export const labellers = [
  "COMMENT",
  "NAME",
  "PREP",
  "PUNC",
  "PURPOSE",
  "QTY",
  "SIZE",
  "UNIT",
  "OTHER"
] as const;

export type LabellerCategory = typeof labellers[number];

export interface Amount {
  APPROXIMATE: boolean
  MULTIPLIER: boolean
  RANGE: boolean
  SINGULAR: boolean
  confidence: number
  quantity: number
  quantity_max: number
  starting_index: number
  text: string
  unit: string
}

export type Confidence = {
  confidence: number
  text: string
}

export type Marginals = Record<LabellerCategory, number>

export type Token = [
  string,
  LabellerCategory,
  Marginals | null
]

export interface LabellerProps extends BoxProps {
  identifier?: number | string;
  editMode?: boolean;
  marginalsMode?: boolean;
  tooltipProps?: TooltipProps | {};
  token?: Token;
  size?: "small" | "medium" | "large",
  handler?: UseListStateHandlers<any>,
}

export function Labeller({
  identifier,
  editMode = false,
  marginalsMode = false,
  tooltipProps = {},
  token,
  size = "medium",
  handler,
  ...others
}: LabellerProps) {

  if (!token) return null;

  const [txt, lbl, marginals] = token
  const [editable, setEditable] = useState(lbl)

  const onEditHandler = useCallback((labellerCat: LabellerCategory) => {
    setEditable(labellerCat)
    if(handler && identifier) {
      handler.applyWhere(
        (item) => item.id === identifier,
        (item) => ({
          ...item,
          edited: true,
          tokens: item.tokens.map((tkn: Token) => {
            if(tkn[0] === txt) return [txt, labellerCat]
            else return tkn
          })
        })
      );
    }
  }, [handler, identifier])


  if(editMode) {

    const menuItems = labellers.map((labeller, i) =>
      <>
        <Menu.Item
          component="button"
          className={classes.menuItem}
          onClick={() => onEditHandler(labeller)}
        >
          <Badge variant={labeller}>{labeller}</Badge>
        </Menu.Item>
      </>
    )

    return (
      <Menu position="bottom-start" keepMounted={false}>
        <Menu.Target>
          <Box
            {...others}
            component="button"
            className={cx(classes.labeller, classes.editable)}
            data-labeller={editable}
            data-size={size}
          >
            <span>{txt}</span>
            <IconSelector size={16} />
          </Box>
        </Menu.Target>

        <Menu.Dropdown>
          {menuItems}
        </Menu.Dropdown>
      </Menu>
    )
  }

  if(marginalsMode && marginals) {
    const marginalRows = Object.keys(marginals).map(category => (
      <Flex justify="space-between" gap="var(--small-spacing)">
        <div>{category}</div>
        <div>{(marginals[category as LabellerCategory] * 100).toFixed(2)}</div>
      </Flex>
    ))
    return (
      <Tooltip {...tooltipProps} label={marginalRows}>
        <Box
          {...others}
          component="span"
          className={cx(classes.labeller, classes.marginable)}
          data-labeller={lbl}
          data-size={size}
        >
          {txt}
        </Box>
      </Tooltip>
    )
  }

  return (
    <Box
      {...others}
      component="span"
      className={cx(classes.labeller)}
      data-labeller={lbl}
      data-size={size}
    >
      {txt}
    </Box>
  )
}
