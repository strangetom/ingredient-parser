// {{{EXTERNAL}}}

import { Box, type BoxProps, CopyButton, Text } from "@mantine/core";
import type { UseListStateHandlers } from "@mantine/hooks";
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
import { useCallback, useState } from "react";
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
	handler?: Omit<UseListStateHandlers<ParsedSentenceEditable>, "setState"> & {
		set: (items: ParsedSentenceEditable[]) => void;
	};
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
	const [deletion, setDeletion] = useState(sentence?.removed || false);
	const [edited] = useState(sentence?.edited || false);
	const [plain, setPlain] = useState(false);

	const onSetForRemovalHandler = useCallback(() => {
		setDeletion((o) => !o);
		if (handler) {
			handler.applyWhere(
				(item) => item.id === sentence.id,
				(item) => ({ ...item, removed: true }),
			);
		}
	}, [handler, sentence.id]);

	const onRevertRemovalHandler = useCallback(() => {
		setDeletion((o) => !o);
		if (handler) {
			handler.applyWhere(
				(item) => item.id === sentence.id,
				(item) => {
					const clone = item;
					delete clone.removed;
					return { ...clone };
				},
			);
		}
	}, [handler, sentence.id]);

	const labellers = sentence.tokens.map((tkn, i) => (
		<Labeller
			key={`sentence-token-${tkn}`}
			position={i % 2 === 0 ? "top" : "bottom"}
			token={tkn}
			handler={handler}
			identifier={sentence.id}
			{...labellerProps}
		/>
	));

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
		>
			<Box
				data-deletion={deletion || undefined}
				data-edited={edited || undefined}
				className={classes.root}
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
									onClick={() => setPlain(false)}
									text="View tokens"
								/>
							) : (
								<ActionIconTooltipped
									iconography={IconEye}
									onClick={() => setPlain(true)}
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
							(deletion ? (
								<ActionIconTooltipped
									iconography={IconTrashXFilled}
									onClick={onRevertRemovalHandler}
									text="Undo removal"
									actionIconProps={{ color: "red" }}
								/>
							) : (
								<ActionIconTooltipped
									iconography={IconTrash}
									onClick={onSetForRemovalHandler}
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
