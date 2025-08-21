# Requirements

Requires [Node](https://nodejs.org/en/download/package-manager), [Vite](https://vite.dev/guide/#manual-installation), & [Typescript](https://www.typescriptlang.org/download/)

# Development/Setup

Install npm packages

```
npm i
```

Build bundle (required to watch for file changes during dev)

```
npx vite build --watch
```

Start the flask server at root

```
export PYTHONPATH=. && FLASK_APP=webtools/app.py flask run --debug
```
