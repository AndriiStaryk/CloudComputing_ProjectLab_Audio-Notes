# Google Cloud Setup Tutorial

This tutorial will guide you through setting up Google Cloud Platform for the Audio Notes application, including Speech-to-Text and Gemini API.

## Table of Contents
1. [Create Google Cloud Project](#1-create-google-cloud-project)
2. [Enable Required APIs](#2-enable-required-apis)
3. [Set Up Billing](#3-set-up-billing)
4. [Create Service Account](#4-create-service-account)
5. [Get Gemini API Key](#5-get-gemini-api-key)
6. [Configure Application](#6-configure-application)
7. [Test Your Setup](#7-test-your-setup)

---

## 1. Create Google Cloud Project

### Step 1.1: Go to Google Cloud Console
1. Open your browser and go to: https://console.cloud.google.com/
2. Sign in with your Google account

### Step 1.2: Create New Project
1. Click on the project dropdown at the top of the page (next to "Google Cloud")
2. Click **"New Project"** button
3. Enter project details:
   - **Project name**: `audio-notes-app` (or your preferred name)
   - **Organization**: Leave as default (No organization)
   - **Location**: Leave as default
4. Click **"Create"**
5. Wait for the project to be created (you'll see a notification)
6. **Important**: Note down your **Project ID** (it will be shown in the project selector)

---

## 2. Enable Required APIs

### Step 2.1: Enable Cloud Speech-to-Text API
1. With your new project selected, click on the **hamburger menu** (☰) in the top-left
2. Navigate to: **APIs & Services** > **Library**
3. In the search bar, type: `Speech-to-Text`
4. Click on **"Cloud Speech-to-Text API"**
5. Click the blue **"Enable"** button
6. Wait for the API to be enabled (takes a few seconds)

### Step 2.2: Enable Generative Language API (for Gemini)
1. Still in the API Library, search for: `Generative Language API`
2. Click on **"Generative Language API"**
3. Click **"Enable"**
4. Wait for the API to be enabled

### Step 2.3: Verify APIs are Enabled
1. Go to: **APIs & Services** > **Enabled APIs & services**
2. You should see both:
   - Cloud Speech-to-Text API
   - Generative Language API

---

## 3. Set Up Billing

**Note**: Both Speech-to-Text and Gemini offer free tiers, but billing must be enabled.

### Step 3.1: Enable Billing
1. Go to: **Billing** (from hamburger menu)
2. If you don't have a billing account:
   - Click **"Link a billing account"**
   - Click **"Create billing account"**
   - Enter your payment information
   - Google offers $300 free credit for new users
3. Link your billing account to the project

### Free Tier Limits:
- **Speech-to-Text**: 60 minutes per month free
- **Gemini API**: Rate-limited free tier available

---

## 4. Create Service Account

Service accounts allow your application to authenticate with Google Cloud.

### Step 4.1: Navigate to Service Accounts
1. From the hamburger menu, go to: **IAM & Admin** > **Service Accounts**
2. You should see your project name at the top

### Step 4.2: Create Service Account
1. Click **"+ Create Service Account"** at the top
2. Fill in the details:
   - **Service account name**: `audio-notes-service`
   - **Service account ID**: (auto-generated, like `audio-notes-service@your-project.iam.gserviceaccount.com`)
   - **Description**: `Service account for audio notes app`
3. Click **"Create and Continue"**

### Step 4.3: Grant Roles
1. Click on **"Select a role"** dropdown
2. Add the following roles one by one:
   
   **First Role:**
   - Type `Speech` in the search
   - Select: **Cloud Speech-to-Text API User** (or **Cloud Speech Client**)
   - Click **"+ Add Another Role"**
   
   **Second Role:**
   - Type `AI Platform` in the search
   - Select: **AI Platform User**
   
3. Click **"Continue"**

### Step 4.4: Skip Optional Settings
1. Skip the "Grant users access" section (not needed)
2. Click **"Done"**

### Step 4.5: Create JSON Key
1. You'll see your new service account in the list
2. Click on the **email address** of your service account
3. Go to the **"Keys"** tab
4. Click **"Add Key"** > **"Create new key"**
5. Select **JSON** format
6. Click **"Create"**
7. A JSON file will download automatically - **Save this file securely!**
8. Rename the file to something simple like: `service-account-key.json`

**⚠️ Important Security Notes:**
- Never commit this JSON file to Git
- Never share this file publicly
- Keep it secure - it provides full access to your project
- The file is already in `.gitignore`

---

## 5. Get Gemini API Key

### Option A: Google AI Studio (Recommended for Development)

1. Go to: https://makersuite.google.com/app/apikey
2. Sign in with the same Google account
3. Click **"Create API Key"**
4. Select your Google Cloud project: `audio-notes-app`
5. Click **"Create API Key in Existing Project"**
6. Copy the API key (starts with `AIza...`)
7. **Save this key** - you'll need it for configuration

### Option B: Google Cloud Console

1. In Google Cloud Console, go to: **APIs & Services** > **Credentials**
2. Click **"+ Create Credentials"** > **"API Key"**
3. Copy the API key
4. (Optional) Click **"Restrict Key"** to limit it to Generative Language API

---

## 6. Configure Application

### Step 6.1: Prepare Configuration
1. Navigate to your project directory:
   ```bash
   cd /Users/andreystarik/Developer/University/semester7/CloudComputing/presentation_lab
   ```

2. Copy your service account JSON key to the project directory:
   ```bash
   # Example:
   cp ~/Downloads/service-account-key.json .
   ```

### Step 6.2: Create .env File
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your favorite editor:
   ```bash
   nano .env
   # or
   code .env
   ```

3. Fill in your credentials:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
   GOOGLE_CLOUD_PROJECT_ID=audio-notes-app
   GEMINI_API_KEY=AIzaSy...your-actual-key...
   ```

4. Save and close the file

### Step 6.3: Verify File Paths
Make sure your service account JSON file is in the correct location:
```bash
ls -la service-account-key.json
```

---

## 7. Test Your Setup

### Step 7.1: Install Dependencies
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install required packages
pip install -r requirements.txt
```

**Note for macOS**: You may need to install PortAudio for pyaudio:
```bash
brew install portaudio
```

### Step 7.2: Test Google Cloud Authentication
Create a test script `test_setup.py`:

```python
import os
from dotenv import load_dotenv
from google.cloud import speech
import google.generativeai as genai

load_dotenv()

print("Testing Google Cloud setup...")
print(f"Project ID: {os.getenv('GOOGLE_CLOUD_PROJECT_ID')}")
print(f"Credentials: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

# Test Speech-to-Text
try:
    client = speech.SpeechClient()
    print("✅ Speech-to-Text API: Connected successfully!")
except Exception as e:
    print(f"❌ Speech-to-Text API: Failed - {e}")

# Test Gemini
try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Say 'Hello, test successful!'")
    print(f"✅ Gemini API: {response.text}")
except Exception as e:
    print(f"❌ Gemini API: Failed - {e}")
```

Run the test:
```bash
python test_setup.py
```

If both tests pass, you're ready to go! 🎉

### Step 7.3: Run the Application
```bash
python main.py
```

---

## Troubleshooting

### Error: "Could not load credentials"
- Check that `GOOGLE_APPLICATION_CREDENTIALS` path is correct
- Verify the JSON file exists and is readable
- Use absolute path if relative path doesn't work

### Error: "API has not been enabled"
- Go back to Google Cloud Console
- Check **APIs & Services** > **Enabled APIs & services**
- Make sure both APIs are enabled

### Error: "Permission denied"
- Verify your service account has the correct roles
- Go to **IAM & Admin** > **IAM**
- Find your service account and check permissions

### Error: "Billing must be enabled"
- Go to **Billing** in Google Cloud Console
- Link a billing account to your project
- Free tier is sufficient for development

### PyAudio Installation Issues (macOS)
```bash
# Install PortAudio first
brew install portaudio

# Then install pyaudio
pip install pyaudio
```

### PyAudio Installation Issues (Linux)
```bash
# Ubuntu/Debian
sudo apt-get install portaudio19-dev python3-pyaudio

# Then install pyaudio
pip install pyaudio
```

---

## Cost Considerations

### Free Tier Limits
- **Speech-to-Text**: 60 minutes/month free
- **Gemini API**: Limited free usage
- After free tier, costs are:
  - Speech-to-Text: ~$0.024 per minute
  - Gemini: Varies by usage

### Tips to Stay in Free Tier
1. Use short test recordings during development
2. Monitor usage in Google Cloud Console
3. Set up billing alerts
4. Consider using cached results for testing

---

## Next Steps

1. ✅ Complete this setup tutorial
2. ✅ Run the test script
3. ✅ Launch the application
4. 📝 Create your first audio note!

---

## Additional Resources

- [Google Cloud Speech-to-Text Documentation](https://cloud.google.com/speech-to-text/docs)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Google Cloud Python Client Library](https://cloud.google.com/python/docs/reference)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/best-practices-service-accounts)

---

## Support

If you encounter issues:
1. Check the error message carefully
2. Verify all steps in this tutorial
3. Check Google Cloud Console for API status
4. Review application logs
5. Ensure billing is enabled and APIs are active

Good luck with your audio notes app! 🎵📝
