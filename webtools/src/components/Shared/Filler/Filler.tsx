// {{{EXTERNAL}}}
import React, {  } from 'react';
import { Center, Text } from '@mantine/core';
// {{{ASSETS}}}
import { ReactComponent as Bowl } from "../../../assets/bowl.svg"
import { ReactComponent as Sandwich } from "../../../assets/sandwich.svg"
// {{{STYLES}}}
import { default as classes } from './Filler.module.css';

const svgIllustrations = [
  "bowl",
  "sandwich"
] as const;

const svgIllutrationsMapped = [
  { id: "bowl", component: Bowl},
  { id: "sandwich", component: Sandwich},
]

export type SVGIllustration = typeof svgIllustrations[number];

export function Filler({
  text,
  illustration,
  children
}: {
  text: string,
  illustration: SVGIllustration,
  children?: React.ReactNode
}) {

    const Illo = svgIllutrationsMapped.find(illo => illo.id === illustration)!.component

   return (
     <Center className={classes.root}>
        <Illo className={classes.illustration} />
        <Text className={classes.text}>{text}</Text>
        {children}
    </Center>
   )
 }
