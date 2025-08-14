interface EndpointsDef {
	base: string;
	websocket: string;
	basePort: string;
	websocketPort: string;
	paths: Record<Path, string>;
}

const Endpoints = {
	base: import.meta.env.FLASK_SERVER_ADDRESS || "http://127.0.0.1",
	websocket: import.meta.env.FLASK_SERVER_ADDRESS || "ws://127.0.0.1",
	basePort: import.meta.env.FLASK_SERVER_PORT || "5000",
	websocketPort: import.meta.env.FLASK_SERVER_PORT || "5001",
	paths: {
		parser: "/parser",
		precheck: "/precheck",
		labellerSearch: "/labeller/search",
		labellerSave: "/labeller/save",
		labellerPreUpload: "/labeller/preupload",
		labellerAvailableSources: "/labeller/available-sources",
		labellerBulkUpload: "/labeller/bulk-upload",
		trainerConnect: "/",
	},
} as EndpointsDef;

const pathStrings: string[] = [...Object.keys(Endpoints.paths)] as const;
type Path = (typeof pathStrings)[number];

interface ConstructEndpointOpts {
	path: Path;
	hasPort?: boolean;
	isWebSocket?: boolean;
}

export const constructEndpoint = ({
	path,
	hasPort = true,
	isWebSocket = false,
}: ConstructEndpointOpts): string => {
	try {
		const keys = Object.keys(Endpoints.paths);
		if (!keys.includes(path)) throw `Path ${path as string} not available`;

		const base = isWebSocket ? Endpoints.websocket : Endpoints.base;
		const urlNoPort = base + Endpoints.paths[path];
		const urlWithPort =
			base +
			":" +
			(isWebSocket ? Endpoints.websocketPort : Endpoints.basePort) +
			Endpoints.paths[path];

		return hasPort ? urlWithPort : urlNoPort;
	} catch {
		return Endpoints.base;
	}
};
