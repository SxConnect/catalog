# SixPet Catalog - Frontend

Next.js 14 frontend for the SixPet Catalog Engine.

## Features

- 🔐 NextAuth authentication
- 🌓 Dark/Light theme toggle
- 📤 Drag & drop PDF upload
- 🔑 API key management with usage visualization
- ⚙️ Settings for web scraping and processing
- 📊 Dashboard with statistics

## Development

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Environment Variables

See `.env.example` for required variables.

## Production

Built automatically via GitHub Actions and deployed as Docker image:
`ghcr.io/sxconnect/catalog-frontend:latest`

See main repository README for deployment instructions.
