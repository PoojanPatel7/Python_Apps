# 🧠 VisionMind — Offline Image Intelligence Analyzer

A local, no-API image analysis application that performs heuristic-based color analysis, texture detection, complexity scoring, and composition analysis — all without any cloud services.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-0078D6)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **100% offline** — No API keys, no internet, no cloud
- **Color analysis** — Dominant colors, color palette extraction, harmony detection
- **Texture analysis** — Pattern recognition, smoothness/roughness scoring
- **Complexity scoring** — Edge density, detail level, visual weight
- **Composition analysis** — Rule of thirds, symmetry, visual balance
- **Custom dark UI** — Built with tkinter, obsidian-inspired theme
- **Image statistics** — Resolution, aspect ratio, file size, color space

---

## 🛠️ Setup & Installation

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python image_ai_app.py
```

### Step 3: Load an Image
Click "Open Image" and select any JPG, PNG, BMP, or TIFF file.

---

## 📦 Dependencies

| Package  | Purpose                              |
|----------|--------------------------------------|
| `Pillow` | Image loading and manipulation       |
| `numpy`  | Numerical computations for analysis  |

---

## 📂 File Structure

```
06_Image_AI_Analyzer/
├── image_ai_app.py     # Main application (ImageAnalyzer class)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 🔧 How It Works

The app uses **custom heuristic algorithms** (no ML models):

1. **Color Analysis** — Uses K-means-like clustering on pixel data to extract dominant colors
2. **Texture Detection** — Calculates variance in local pixel neighborhoods
3. **Edge Detection** — Applies Sobel-like gradient filters to measure complexity
4. **Composition** — Divides image into thirds and measures visual weight distribution
5. **Harmony** — Analyzes color wheel positions of dominant colors for harmony type

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
