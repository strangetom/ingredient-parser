import React, { useEffect } from "react"
import { useTabLabellerStore } from "../../../domain"
import { useShallow } from "zustand/react/shallow"

export function FetchAvailableSouceListener(){
  const {
    fetchAvailableSourcesApi
  } = useTabLabellerStore(
    useShallow((state) => ({
      fetchAvailableSourcesApi: state.fetchAvailableSourcesApi
    })),
  )

  useEffect(() => {
    fetchAvailableSourcesApi()
  }, [])

  return <React.Fragment />
}
