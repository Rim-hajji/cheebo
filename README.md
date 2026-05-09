# 🐾 Cheebo Healthcare Application

This repository contains the complete fullstack application for Cheebo Healthcare, broken down into two main parts: the Python Backend and the Flutter Mobile Frontend.

## 1. 🐍 Running the Backend (Python FastAPI)

Wait for the backend to be running before testing the frontend.

1. Open your terminal in the root folder (`module_docto_agent`).
2. Make sure you have installed the requirements:
   ```bash
   py -m pip install -r requirements.txt
   ```
3. Boot the FastAPI server:
   ```bash
   py -m backend.api.main
   ```
4. You should see `Uvicorn running on http://0.0.0.0:8000`. The server is now waiting for requests.

---

## 2. 📱 Running the Frontend (Flutter Mobile App)

You must have the **Flutter SDK** installed on your machine to run the mobile app. (If you don't have it, download it from [flutter.dev](https://docs.flutter.dev/get-started/install)).

1. Open a **new terminal tab** (leave the backend running).
2. Go into the frontend folder:
   ```bash
   cd frontend
   ```
3. Get the required Dart packages (like `speech_to_text`, `http`, etc.):
   ```bash
   flutter pub get
   ```
4. Run the application (choose the platform you prefer):
   - **For Web (Chrome):** `flutter run -d chrome`
   - **For Android Emulator / Physical Device:** `flutter run`
   - **For Windows Desktop:** `flutter run -d windows`

### 🔌 API Connection Note (Android Emulator only)
If you run this on a real Android Emulator, remember that `127.0.0.1` points to the phone's internal localhost, not your computer's localhost. 
If it fails to connect, simply open `frontend/lib/services/api_service.dart` and change `http://127.0.0.1:8000/api/v1` to `http://10.0.2.2:8000/api/v1`.
