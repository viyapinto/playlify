# Playlify

**Playlify** is an interactive visual research laboratory exploring the relationship between album cover artwork and musical genre classification using Machine Learning.

## Research Question
Can we predict the musical genre of an album based purely on its cover artwork? 

This project explores feature extraction, clustering, and classification techniques to build an offline research pipeline, culminating in a responsive, interactive web application that allows users to upload any image and visualize the prediction and similarity search process.

## Technology Stack

- **Frontend:** React, Vite, TypeScript, Vanilla CSS
- **Backend:** Python, FastAPI, Uvicorn
- **Machine Learning (Offline):** scikit-learn, OpenCV/Pillow, Pandas, NumPy

## Repository Structure

- `backend/` - The production FastAPI service handling image inference and serving predictions.
- `frontend/` - The React application providing the interactive user interface.
- `research/` - (Offline) Scripts and notebooks for data cleaning, EDA, feature extraction, PCA, and model training.

## Local Setup

### Backend (Local Development)
1. Navigate to the `backend/` directory.
2. Install dependencies (e.g. `pip install -r requirements.txt`).
3. Run the development server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend (Local Development)
1. Navigate to the `frontend/` directory.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Set your environment variables in `.env` (see DEPLOYMENT.md for details):
   ```
   VITE_API_URL=http://localhost:8000
   ```
4. Start the Vite development server:
   ```bash
   npm run dev
   ```

## Deployment
For detailed deployment instructions for both frontend and backend environments, please refer to [DEPLOYMENT.md](./DEPLOYMENT.md).
