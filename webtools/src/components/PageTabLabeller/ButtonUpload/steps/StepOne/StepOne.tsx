// {{{EXTERNAL}}}
import {
	Box,
	Center,
	Flex,
	Group,
	Loader,
	SegmentedControl,
	Text,
	Textarea,
} from "@mantine/core";
import { Dropzone, type FileWithPath } from "@mantine/dropzone";
// {{{ASSETS}}}
import { IconCheck, IconFileTextFilled, IconX } from "@tabler/icons-react";
import type React from "react";
import { useEffect, useRef } from "react";
import { useShallow } from "zustand/react/shallow";
import { useUploadNewLabellersStore } from "../../../../../domain";
// {{{EXTERNAL}}}
import { Sectionable } from "../../../../Shared";
// {{{STYLES}}}
import classes from "./StepOne.module.css";

export function StepOne() {
	const { rawText, importingRawText, files, uploadOption, setState } =
		useUploadNewLabellersStore(
			useShallow((state) => ({
				rawText: state.rawText,
				importingRawText: state.importingRawText,
				files: state.files,
				uploadOption: state.uploadOption,
				setState: state.setState,
			})),
		);

	const timeoutRef = useRef(-1);

	const onDropHandler = (files: FileWithPath[]) => {
		const file = files[0];
		const reader = new FileReader();

		const parseCSV = (event: ProgressEvent<FileReader>) => {
			if (event.target?.result) {
				const content = event.target.result.toString();
				const lines = content
					.split("\n")
					.map((line: string) => line.trim().replaceAll('"', ""));
				setState({ rawText: lines.join("\n"), files: files });
			}
		};

		const parseTxt = (event: ProgressEvent<FileReader>) => {
			if (event.target?.result) {
				const content = event.target.result.toString();
				setState({ rawText: content, files: files });
			}
		};

		reader.onload = (event: ProgressEvent<FileReader>) => {
			setState({ importingRawText: true });
			if (file.type === "text/plain") parseTxt(event);
			if (file.type === "text/csv") parseCSV(event);
		};

		reader.onloadend = () => {
			timeoutRef.current = window.setTimeout(
				() => setState({ importingRawText: false }),
				600,
			);
		};

		reader.onabort = () => {
			window.clearTimeout(timeoutRef.current);
		};

		reader.onerror = () => {
			window.clearTimeout(timeoutRef.current);
		};

		reader.readAsText(file);
	};

	const onUploadOptionHandler = (value: string) =>
		setState({ uploadOption: value as string });
	const onRawTextChangeHandler = (
		event: React.ChangeEvent<HTMLTextAreaElement>,
	) => {
		setState({ rawText: event.target.value });
	};

	useEffect(() => {
		return () => {
			window.clearTimeout(timeoutRef.current);
		};
	}, []);

	return (
		<Sectionable.Section padded full>
			<Box className={classes.root}>
				<Box className={classes.toggler}>
					<SegmentedControl
						value={uploadOption}
						onChange={onUploadOptionHandler}
						data={[
							{ label: "Copy & Paste", value: "copy.paste" },
							{ label: "Upload Text File", value: "attach.file" },
						]}
					/>
				</Box>
				{uploadOption === "copy.paste" && (
					<Textarea
						placeholder="Paste ingredients here"
						value={rawText}
						onChange={onRawTextChangeHandler}
						classNames={{
							input: classes.textAreaInput,
							wrapper: classes.textAreaWrapper,
							root: classes.textAreaRoot,
						}}
					/>
				)}
				{uploadOption === "attach.file" && (
					<Box className={classes.dropzone}>
						<Dropzone
							disabled={importingRawText}
							accept={{
								"text/csv": [".csv"],
								"text/plain": [".txt"],
							}}
							multiple={false}
							onDrop={onDropHandler}
							classNames={{
								inner: classes.dropZoneInner,
								root: classes.dropZoneRoot,
							}}
						>
							<Center className={classes.dropZoneCenter}>
								<Group justify="center" gap="sm" wrap="nowrap">
									<Box style={{ height: 30, width: 30 }}>
										{importingRawText ? (
											<Flex>
												<Loader color="var(--fg)" size={24} />
											</Flex>
										) : (
											<>
												<Dropzone.Accept>
													<IconCheck size={30} color="var(--fg)" stroke={1.5} />
												</Dropzone.Accept>
												<Dropzone.Reject>
													<IconX size={30} color="var(--fg)" stroke={1.5} />
												</Dropzone.Reject>
												<Dropzone.Idle>
													<IconFileTextFilled
														size={30}
														color="var(--fg)"
														stroke={1.5}
													/>
												</Dropzone.Idle>
											</>
										)}
									</Box>

									{files && files.length !== 0 ? (
										files.map((file) => (
											<div>
												<Text variant="light" inline>
													{file.name}
												</Text>
											</div>
										))
									) : (
										<div>
											<Text variant="light" inline>
												Drop your plain text file or click here
											</Text>
											<Text size="sm" variant="light" inline mt={7}>
												Supports .txt and .csv files
											</Text>
										</div>
									)}
								</Group>
							</Center>
						</Dropzone>
					</Box>
				)}
			</Box>
		</Sectionable.Section>
	);
}
