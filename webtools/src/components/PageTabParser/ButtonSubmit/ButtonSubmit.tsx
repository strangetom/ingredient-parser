// {{{EXTERNAL}}}
import React, {  } from "react"
import { Button, ButtonProps } from "@mantine/core"
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { useTabParserStore } from "../../../domain";

export function ButtonSubmit(props: ButtonProps){

  const {
    input,
    loading,
    getParsedApi
  } = useTabParserStore(
    useShallow((state) => ({
      input: state.input,
      loading: state.loading,
      getParsedApi: state.getParsedApi
    })),
  )

  return (
    <Button
      variant="dark"
      h={50}
      onClick={() => getParsedApi({ shouldAddToHistory: true })}
      disabled={input.sentence.trim().length === 0}
      loading={loading}
    >
      Submit
    </Button>
  )
}
