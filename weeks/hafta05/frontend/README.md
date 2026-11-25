# LogScope React frontend

19 routed screens, shared navigation, Figma-aligned colour/typography direction, API-backed actions and labelled demo fallbacks.

```
npm install
npm run dev
```

Start FastAPI `backend.fullstack:app` on port 8000 first. Vite will proxy `/api` calls to it; without a server, the UI will show **local demo** data. For a build:

```
npm run build
```

Static syntax test `npm run check:jsx` uses TypeScript from devDependencies. `npm run check:routes` checks the route inventory. No npm installation/build could be executed in the sandbox because public registry access was unavailable. The standalone HTML has passed 19/19 browser route tests.
