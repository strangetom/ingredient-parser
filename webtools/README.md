# Requirements and Setup

See repository's main README.md

# Development Ethos

Similar to the Ingredient Parser library itself, the webtools runtime runs locally without any remote resources or requests. Build or compile time might require fetching resources required for tooling (e.g. BiomeJS formatting); this will depend on your local machine's setup. The development ethos of "runtime local" is encouraged for any future code contributions.

# Built With

The web technology stack (packages, libraries, & tooling) includes: [Typescript](https://www.typescriptlang.org/), [React](https://react.dev/), [Mantine](https://mantine.dev/), [Zustand](https://zustand-demo.pmnd.rs/), [Socket.IO](https://socket.io/), [Vite](https://vite.dev/), [BiomeJS](https://biomejs.dev/), [Flask](https://flask.palletsprojects.com/en/stable/), [Flask-SocketIO](https://flask-socketio.readthedocs.io/en/latest/), and [Flask-CORS](https://corydolphin.com/flask-cors/) (_subject to change; only for informational purposes_)

# Client (TS/React/Vite)

The file naming schema for client components, state/store, and/or directories align with the actual tabs (i.e. pages) within the user interface. For example, feature-to-naming may appear similar to the following:

| Feature/Page | Directory | Component | State/Store |
| :--- | :--- | :--- | :--- |
| Try the Parser | /PageTabParser/ | MainTryParser.tsx | tabParserStore.ts |
| Browse & Label | /PageTabLabeller/ | MainLabeller.tsx | tabLabellerStore.ts |
| Train the Model | /PageTabTrain/ | MainTrainModel.tsx | tabTrainStore.ts |


# Server (Flask)

Multiple flask server instances support API requests from the client. The primary flask server `app.py` handles most requests with the Ingredient Parser library for the parsing and labelling features. The secondary flask server `app.sockets.py` uses web sockets to run the training features within the library, and pipe asynchronous updates to the client.

```
PageTabLabeller
PageTabParser
PageTabTrain
```
