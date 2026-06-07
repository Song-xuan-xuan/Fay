# Fay Vue Frontend

Vue 3 + Vite frontend for the Fay management console.

## Commands

```powershell
npm install
npm run dev
npm run build
npm test -- src/utils/messageStream.test.ts
```

## Environment

- `VITE_API_BASE_URL`: Flask backend URL used by Vite proxy. Default: `http://127.0.0.1:5000`.
- `VITE_WS_URL`: Fay web console WebSocket URL. Default: `ws://<host>:10003`.
- `VITE_LIVE2D_URL`: Live2D iframe URL. Default: `http://127.0.0.1:5174`. Keep this separate from the Fay console URL to avoid iframe nesting.

## Production Serving

`npm run build` writes `dist/`. The Flask server now serves `fay-frontend/dist/index.html` for `/`, `/setting`, and `/live2d` when it exists. If the Vue build is missing, Flask falls back to the legacy Jinja templates.
