// {{{ EXTERNAL }}}
import React from "react";
import ReactDOM from "react-dom/client";
import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";
// {{{ INTERNAL }}}
import "./styles/css/index.css";
import "./styles/css/primitives.css";
import "./styles/css/colours.css";
import "./styles/css/animate.css";
import App from "./App";

const root = ReactDOM.createRoot(
	document.getElementById("root") as HTMLElement,
);

root.render(
	<React.StrictMode>
		<App />
	</React.StrictMode>,
);
