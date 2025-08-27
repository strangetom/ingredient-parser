## Requirements and Setup

To run the web app, follow the prior steps on `requirements-dev.txt`, and separately install [Node](https://nodejs.org/en/download), the JS runtime, on your machine. Lastly, navigate to the webtools directory and run the following commands:

```bash
$ npm install
$ npm run dev
```

The compiler will build a react/typescript bundle through `vite`, and the runtime will serve up a backend through `flask` that handles the static html and basic API requests on one instance (port), and web socket API requests on another instance (port).

## Development Ethos & Stack

Similar the `Ingredient Parser` python library, the webtools package, at runtime, does not require any remote resources or outside server requests. During compile or buildtime after installation, the tooling libraries may require fetching remote resources, for example BiomeJS for code formatting. This behavior may depend on your local machine's configuration. The web technology stack (packages, libraries, & tooling) includes: [Typescript](https://www.typescriptlang.org/), [React](https://react.dev/), [Mantine](https://mantine.dev/), [Zustand](https://zustand-demo.pmnd.rs/), [Vite](https://vite.dev/), [BiomeJS](https://vite.dev/), [Socket.IO](https://socket.io/), [Flask](https://flask.palletsprojects.com/en/stable/), [Flask-SocketIO](https://flask-socketio.readthedocs.io/en/latest/), and [Flask-CORS](https://corydolphin.com/flask-cors/)


## Code Heirarchy

The heirarchy adheres to a WYSIWYG structure. The client has three main feature tabs, i.e. pages, which includes the parser, labeller, and trainer. The flask server runs two separate instances `app.py` (for most html/API requests) and `app.sockets.py` (for training API requests). Training the models is resource intenstive and has unique logging behavior, both of which necessitate a separate web socket server.

```
assets
  | {images}

components
  | {labeller} > "browse & label" UI components
  | {parser} > "try the parser" UI components
  | {train} > "train the model" UI components
  | shared

domain
  | api > endpoint resolvers
  | collections > static data lists or jsons
  | store > zustrand store for app state
  | types > typescript interfaces

styles
  | css > custom styling
  | mantine > vendor specific styling

app.py > runs the basic api server
app.sockets.py > runs the web socket server
```

## Screenshots

| Parser | Labeller | Trainer |
| :------- | :------- | :------- |
| ![Screen shot of web parser](./../docs/source/_static/webtools/app.parser.screenshot.png)     | ![Screen shot of web labeller](./../docs/source/_static/webtools/app.labeller.screenshot.png)     | ![Screen shot of web trainer](./../docs/source/_static/webtools/app.trainer.screenshot.png)   |
