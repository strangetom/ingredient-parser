// {{{EXTERNAL}}}
import React, {  } from "react"
import { Badge, Breadcrumbs, Table, TableTrProps } from "@mantine/core"
// {{{INTERNAL}}}
import { Amount, Confidence, FoundationFood, LabellerCategory } from "../../../../../domain";

interface TableRowProps extends TableTrProps {
  title: string,
  badgeCategory: LabellerCategory,
  items: Confidence[] | FoundationFood[] | Amount[]
}


export function TableRow({
  title,
  badgeCategory,
  items,
  ...others
}: TableRowProps){

  return (
    <Table.Tr {...others}>
      <Table.Td width={100} fw="bold">{title}</Table.Td>
        <Table.Td>
          <Breadcrumbs separator="●" separatorMargin="xs" styles={{ breadcrumb: { marginTop: 2, marginBottom: 2}, separator: { color: "var(--fg)"}}}>
            {items.map(({ text, confidence }, i) =>
              <span key={"tr-span-" + i} style={{ fontSize: "var(--mantine-font-size-md)" }}>
                {text}
                {confidence !== 0 && <Badge ml={6} variant={badgeCategory}>{(confidence * 100).toFixed(2)}%</Badge>}
              </span>
            )}
          </Breadcrumbs>
      </Table.Td>
    </Table.Tr>
  )
}
