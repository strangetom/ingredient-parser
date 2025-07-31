// {{EXTERNAL}}
import { useEffect } from 'react'
import { useShallow } from 'zustand/react/shallow'
// {{INTERNAL}}
import { useAppShellStore } from '../../../domain'
import { Box, Code, Divider, LoadingOverlay, Modal, Stack, Text, Title } from '@mantine/core';
// {{STYLES}}
import classes from "./TrainPreCheckListener.module.css"

export function TrainPreCheckListener() {

  const {
    precheckPackages,
    prechecking,
    precheckValid,
    fetchPreCheck
  } = useAppShellStore(
    useShallow((state) => ({
      precheckPackages: state.precheckPackages,
      prechecking: state.prechecking,
      precheckValid: state.precheckValid,
      fetchPreCheck: state.fetchPreCheck
    })),
  )

  useEffect(() => {
    fetchPreCheck()
  }, []);


  return prechecking ? (
    <LoadingOverlay
      visible={true}
      zIndex={99999}
      overlayProps={{ blur: 2, color: 'var(--bg)' }}
      loaderProps={{ color: "var(--fg)", size: 48, type: 'oval'}}
    />
  ) : (
    <Modal
      withCloseButton={false}
      opened={!precheckValid}
      onClose={() => {}}
      centered
      overlayProps={{  blur: 2, color: 'var(--bg)' }}
      styles={{ body: { padding: 0 }}}
    >
      <div>
        <Box p="md">
          <Text size="lg" fw="bolder" variant="light">
            Packages Missing
          </Text>
          <Text variant="light" lh={1.3}>
            Before you can use the application, please install the missing python packages found in requirements-dev.txt.
          </Text>
          <Box mt="xs" className={classes.codeRoot}>
            {precheckPackages.checks.failed.map(pckg =>
              <Box className={classes.codeLine}>
                {pckg}
              </Box>
            )}
          </Box>
        </Box>
        <Divider />
        <Box p="md">
          <Text size="lg" fw="bolder" variant="light">
            Packages Installed
          </Text>
          <Box mt="xs" className={classes.codeRoot}>
            {precheckPackages.checks.passed.map(pckg =>
              <Box className={classes.codeLine}>
                {pckg}
              </Box>
            )}
          </Box>
        </Box>
      </div>
    </Modal>
  )
}
