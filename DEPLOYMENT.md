# Playlify Deployment Guide

This document outlines the hosting strategy, deployment procedures, and environment configuration for the **Playlify** interactive ML application.

## 1. Hosting Strategy

Playlify uses a separated frontend/backend architecture:
- **Frontend**: A React + Vite Single Page Application (SPA), deployed as a static site.
- **Backend**: A FastAPI Python service, deployed as a public web service exposing a prediction REST API.
- **Data/Models**: The backend holds only the necessary inference artifacts (`scaler.joblib`, `knn_model.joblib`, etc.). Heavy training datasets and images are strictly offline research resources and are **not** deployed.

## 2. Environment Variables

The React frontend communicates with the FastAPI backend via HTTP. Do not hardcode localhost URLs in the frontend code.

Create a `.env` file in the `frontend/` directory:

### Local Development
```env
VITE_API_URL=http://localhost:8000
```

### Production Deployment
```env
VITE_API_URL=https://<your-deployed-fastapi-url>
```

## 3. Local Development

### Backend Startup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Build & Run
```bash
cd frontend
npm install
npm run dev
```

## 4. Production Deployment

### Backend (FastAPI)
1. Ensure `requirements.txt` is updated.
2. Ensure the pre-trained `models/` and necessary `data/` artifacts are present in the `backend/` folder.
3. Deploy the service to a hosting provider that supports Python web services (e.g., Render, Railway, Heroku).
4. **CORS Configuration**: The FastAPI backend is configured to accept requests from the local frontend during development. For production, ensure the backend's CORS settings allow requests from your deployed frontend's origin URL.

### Frontend (React/Vite)
1. Ensure the `VITE_API_URL` environment variable is set to the production backend URL.
2. Build the static site:
   ```bash
   cd frontend
   npm run build
   ```
3. Deploy the resulting `dist/` directory to a static hosting provider (e.g., Vercel, Netlify, GitHub Pages).

## 5. API Verification
To verify the production API is alive and reachable, navigate to the health check endpoint:
`GET https://<your-deployed-fastapi-url>/health`

## 6. Updating the Application
- **ML Updates**: Run the offline research scripts to generate new model artifacts. Copy the updated artifacts to `backend/models/`. Redeploy the backend.
- **UI Updates**: Make changes in `frontend/`. Run `npm run build` and redeploy the frontend static files.

## 7. Limitations
- Uploaded album covers are stored temporarily in memory or a temp directory on the backend for inference, and are deleted immediately after the prediction is returned. 
- The live endpoint cannot retrain models or process the raw MSD-I dataset.
