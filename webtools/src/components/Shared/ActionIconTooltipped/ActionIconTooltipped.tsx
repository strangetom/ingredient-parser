// {{{EXTERNAL}}}
import React, {  } from "react"
import { ActionIcon, Tooltip, TooltipProps, ActionIconProps } from "@mantine/core"
// {{{STYLES}}}
import { Icon, IconProps } from "@tabler/icons-react";


interface ActionIconTooltippedProps  {
  tooltipProps?: Omit<TooltipProps, "children" | "label">,
  actionIconProps?: ActionIconProps,
  onClick?: () => void,
  text: string,
  iconography: React.ForwardRefExoticComponent<IconProps & React.RefAttributes<Icon>>
}

export function ActionIconTooltipped({
  tooltipProps = {
    withArrow: false,
    position: "left",
    style: { padding: "var(--xxsmall-spacing) var(--xsmall-spacing)", fontSize: ".75rem" }
  },
  actionIconProps = {
    variant: "dark"
  },
  onClick,
  text,
  iconography
}: ActionIconTooltippedProps){

  const Iconography = iconography

  return (
    <Tooltip {...tooltipProps} label={text}>
      <ActionIcon {...actionIconProps} onClick={onClick} title={text}>
        <Iconography size={16} />
      </ActionIcon>
    </Tooltip>
  )
}
