# 🏛️ NAKSHAI (AI Floor Plan & Building Map Generator)

An AI-powered architectural floor plan generator and building estimation software supporting **Web (React + Vite + Tailwind + Three.js)**, **Mobile (Flutter)**, and **Backend (Python FastAPI + Free LLM / Geometry Engine)**.

---

## 📸 Mockup & Implementation Match
Designed and engineered exactly to match the **ARCHI-GENIUS WEB** and **ARCHI-GENIUS MOBILE** interface mockup (`image/Gemini_Generated_Image_9w1q599w1q599w1q.png`):
- **Natural Language AI Prompt-to-Map:** Enter plot requirements (e.g., *"Generate 3 Bed, 2 Bath open layout for 50x40 plot"*).
- **2D Interactive CAD Canvas:** Architectural wall thickness, doors with swing arcs, windows, dimension tick marks, and furniture layouts.
- **3D Live Walkthrough Preview:** Isometric extruded 3D room walls (10ft standard height), floor textures, and lighting with orbit controls.
- **Civil Material & Cost Estimator:** Calculates Bricks, Cement bags, Steel tons, Sand, Crush, and Grey Structure budget in PKR and USD.
- **Regional Plot Standards:** Pakistani/South Asian plot presets (3 Marla, 5 Marla, 7 Marla, 10 Marla, 1 Kanal, Custom).
- **Blueprint PDF Export:** Downloadable municipality-ready CAD blueprint.

---

## 🚀 How to Run the Applications

### 1. Backend Engine (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
* API Documentation: `http://localhost:8000/docs`
* Free LLM API Key: Add your Google Gemini API key or Groq API key in `backend/.env`. (Even without an API key, the built-in Smart Architectural Procedural Engine works 100% offline out-of-the-box).

---

### 2. ARCHI-GENIUS Web App (React)
```bash
cd frontend
npm install
npm run dev
```
* Opens in browser at: `http://localhost:3000`

---

### 3. ARCHI-GENIUS Mobile App (Flutter)
```bash
cd mobile
flutter pub get
flutter run
```

---

## 💰 Monetization Modules
1. **Freemium Subscription:** 2 free watermarked blueprints/month; Pro tier for unlimited 3D & vector DXF/DWG exports.
2. **Material Leads Marketplace:** Connecting house builders with local cement, brick, and steel suppliers based on the calculated Bill of Materials (BOM).
3. **Pay-Per-Download Blueprint:** Microtransactions for one-time municipality submission PDF packages.
