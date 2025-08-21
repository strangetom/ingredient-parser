// {{{EXTERNAL}}}
import { useEffect } from "react";
import { useTabLabellerStore } from "../../../domain";

export function FetchAvailableSouceListener() {
	useEffect(() => {
		const fetchAvailableSourcesApi =
			useTabLabellerStore.getState().fetchAvailableSourcesApi;
		fetchAvailableSourcesApi();
	}, []);

	return null;
}
