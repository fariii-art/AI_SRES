# 🚨 SERS — Smart Emergency Response System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**AI-Powered Emergency Dispatch Platform for Pakistan**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [API](#-api)

</div>

---

## 📌 Problem Statement

Pakistan's 1122 Rescue Service handles thousands of calls daily across fire, medical, traffic, crime, flood, and infrastructure emergencies. SERS automates the triage pipeline:

> **Caller submits report (Urdu/English) → AI classifies emergency type → Priority score computed → Nearest available unit dispatched**

---

## ✨ Features

### 🤖 AI Components
- **Bilingual Classification** — Urdu, English, Romanized Urdu support
- **TF-IDF + Logistic Regression** — 92-95% test accuracy
- **Priority Scoring** — Multi-factor scoring (0-100)
- **Smart Routing** — Haversine distance with unit availability tracking

### 👥 User Roles
| Role | Capabilities |
|------|-------------|
| **Reporter** | Submit emergencies, view history |
| **Operator** | View pending, manual dispatch, resolve incidents |
| **Admin** | Analytics, model metrics, fleet management, CSV export |

### 🏥 Emergency Categories
- 🔥 Fire
- 🚗 Traffic Accident
- 🔫 Crime
- 🏥 Medical
- 🌊 Flood
- 🏗️ Infrastructure

### 🗺️ Coverage
- 25+ response units
- 14 Pakistani cities
- Real-time unit availability
- ETA calculation (60 km/h avg speed)

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/fariii-art/SERS_SEMESTER_PROJECT.git
cd SERS_SEMESTER_PROJECT
pip install -r requirements.txt