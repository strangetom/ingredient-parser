// {{{EXTERNAL}}}
import { Button, type ButtonProps } from "@mantine/core";
import { IconTags } from "@tabler/icons-react";
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { useAppShellStore } from "../../../domain";

export function ButtonLabellerDefinitions(props: ButtonProps) {
  const { setLabelDefsModalOpen } = useAppShellStore(
    useShallow((state) => ({
      setLabelDefsModalOpen: state.setLabelDefsModalOpen,
    })),
  );

  return (
    <Button
      variant="dark"
      h={50}
      onClick={() => setLabelDefsModalOpen(true)}
      leftSection={<IconTags />}
      {...props}
    >
      Label definitions
    </Button>
  );
}
