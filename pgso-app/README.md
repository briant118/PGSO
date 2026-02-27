# PPS Palawan Profiling System (Expo App)

Mobile app to scan resident QR codes, view profiles, and download PDFs.

## Setup

1. **Set your server URL** in `config.js`:
   ```js
   export const API_BASE_URL = 'http://192.168.1.32:8000';
   ```
   Replace with your PC's IP (same WiFi as phone).

2. **Start the PPS server** (from main project):
   ```
   runserver-network.bat
   ```

3. **Run the Expo app**:
   ```
   cd pgso-app
   npx expo start
   ```

4. **On your phone**:
   - Install **Expo Go** from Play Store / App Store
   - Scan the QR code shown by `npx expo start`
   - The app opens; tap "Grant Permission" for camera
   - Scan a resident's QR code to view profile and download PDF

## Building for production

- **Android**: `npx expo run:android` or use EAS Build
- **iOS**: Requires Mac; use EAS Build for cloud build
