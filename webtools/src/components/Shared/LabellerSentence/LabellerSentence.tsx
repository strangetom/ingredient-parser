// {{{EXTERNAL}}}

import { Box, type BoxProps, CopyButton, Text } from "@mantine/core";
// {{{ASSETS}}}
import {
	IconCopy,
	IconCopyCheck,
	IconEye,
	IconEyeX,
	IconTrash,
	IconTrashXFilled,
} from "@tabler/icons-react";
import cx from "clsx";
import { useCallback } from "react";
import type { ParsedSentenceEditableHandler } from "../../../domain";
import type { ParsedSentenceEditable } from "../../../domain/types";
// {{{INTERNAL}}}
import { ActionIconTooltipped, Labeller, type LabellerProps } from "../";
// {{{STYLES}}}
import { default as classes } from "./LabellerSentence.module.css";

export const tsk = ["copy", "remove", "plain"] as const;
export type Task = (typeof tsk)[number];

export interface LabellerSentenceProps extends BoxProps {
	sentence: ParsedSentenceEditable;
	tasks?: Task[];
	listable?: boolean;
	labellerProps?: Omit<LabellerProps, "token">;
	handler?: ParsedSentenceEditableHandler;
	index?: number;
}

export function LabellerSentence({
	sentence,
	tasks = [],
	listable,
	handler,
	labellerProps,
	...others
}: LabellerSentenceProps) {
	const { edited, removed, plain } = sentence;

	const onSetHandler = useCallback(
		(attribute: "plain" | "removed" | "edited") => {
			if (handler) {
				handler.applyWhere(
					(item) => item.id === sentence.id,
					(item) => {
						const clone = item;
						return { ...clone, [attribute]: true };
					},
				);
			}
		},
		[handler, sentence.id],
	);

	const onRevertHandler = useCallback(
		(attribute: "plain" | "removed" | "edited") => {
			if (handler) {
				handler.applyWhere(
					(item) => item.id === sentence.id,
					(item) => {
						const clone = item;
						delete clone[attribute];
						return { ...clone };
					},
				);
			}
		},
		[handler, sentence.id],
	);

	const labellers = sentence.tokens.map((tkn, ix) => {
		const [tokenText, tokenLabelCategory] = tkn;
		return (
			<Labeller
				key={`sentence-token-${tokenText}-${tokenLabelCategory}-${ix * 10}`}
				position={ix % 2 === 0 ? "top" : "bottom"}
				token={tkn}
				handler={handler}
				indexIdentifier={ix}
				sentenceIdentifier={sentence.id}
				{...labellerProps}
			/>
		);
	});

	const words = (
		<Text variant="light" fz="1.25em" p="0 calc(var(--small-spacing) / 2)">
			{sentence.sentence}
		</Text>
	);

	const wrapper = tasks ? (
		<Box
			{...others}
			className={cx({
				[classes.listable]: listable,
			})}
			data-deletion={removed || undefined}
			data-edited={edited || undefined}
		>
			<Box
				className={classes.root}
				data-deletion={removed || undefined}
				data-edited={edited || undefined}
			>
				{sentence.id && (
					<Box className={classes.identifable}>{sentence.id}</Box>
				)}
				<Box className={classes.sentence}>{plain ? words : labellers}</Box>
				{tasks.length !== 0 && (
					<Box className={classes.editable}>
						{tasks.includes("plain") &&
							(plain ? (
								<ActionIconTooltipped
									iconography={IconEyeX}
									onClick={() => onRevertHandler("plain")}
									text="View tokens"
								/>
							) : (
								<ActionIconTooltipped
									iconography={IconEye}
									onClick={() => onSetHandler("plain")}
									text="View plain"
								/>
							))}
						{tasks.includes("copy") && (
							<CopyButton value={sentence.sentence}>
								{({ copied, copy }) =>
									copied ? (
										<ActionIconTooltipped
											iconography={IconCopyCheck}
											text="Copied"
										/>
									) : (
										<ActionIconTooltipped
											iconography={IconCopy}
											text="Copy"
											onClick={copy}
										/>
									)
								}
							</CopyButton>
						)}
						{tasks.includes("remove") &&
							(removed ? (
								<ActionIconTooltipped
									iconography={IconTrashXFilled}
									onClick={() => onRevertHandler("removed")}
									text="Undo removal"
									actionIconProps={{ color: "red" }}
								/>
							) : (
								<ActionIconTooltipped
									iconography={IconTrash}
									onClick={() => onSetHandler("removed")}
									text="Mark for removal"
									actionIconProps={{ color: "red" }}
								/>
							))}
					</Box>
				)}
			</Box>
		</Box>
	) : (
		<Box {...others}>
			<Box className={classes.sentence}>{plain ? words : labellers}</Box>
		</Box>
	);

	return wrapper;
}
