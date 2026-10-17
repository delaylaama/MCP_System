# Cloud Provider OAuth 2.0 Integration Guide

This document outlines the real OAuth 2.0 registration, authorization, token exchange, and token lifecycle procedures for Google Drive, Microsoft OneDrive, and Dropbox.

---

## 1. Security Architecture for OAuth Tokens

All access and refresh tokens returned during OAuth consent are **never stored in plaintext**.
- When an OAuth callback is received, tokens are encrypted with Fernet (symmetric authenticated encryption using 128-bit AES in CBC mode with PKCS7 padding and HMAC with SHA256 for authentication).
- The encryption key is loaded from the environment variable `ENCRYPTION_KEY`.
- When an API request needs to communicate with Google, Microsoft, or Dropbox, the token is decrypted dynamically in memory and refreshed automatically if expired.

---

## 2. Google Drive (Google OAuth 2.0)

### 2.1 Google Cloud Console Setup
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project named `Universal-AI-File-Manager`.
3. Enable the **Google Drive API** under **APIs & Services > Library**.
4. Configure the **OAuth Consent Screen**:
   - User Type: External (or Internal if Google Workspace).
   - Scopes: `https://www.googleapis.com/auth/drive.readonly` (or `https://www.googleapis.com/auth/drive.file`).
5. Create **OAuth 2.0 Client ID**:
   - Application Type: Web application.
   - Authorized redirect URIs: `http://localhost:8000/api/providers/google_drive/callback`
6. Add credentials to `.env`:
   ```env
   GOOGLE_CLIENT_ID=your_id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/providers/google_drive/callback
   ```

### 2.2 Google OAuth Flow
1. **Initiate**: `GET /api/providers/google_drive/connect`
   - Generates a cryptographically random `state` parameter bound to the authenticated user ID and stores it in cache or signed token.
   - Redirects the browser to `https://accounts.google.com/o/oauth2/v2/auth`.
2. **Callback**: `GET /api/providers/google_drive/callback?code=...&state=...`
   - Validates the `state` parameter to prevent CSRF attacks.
   - Exchanges `code` via `https://oauth2.googleapis.com/token`.
   - Encrypts `access_token` and `refresh_token`.
   - Stores or updates `ProviderConnection` in the database.
   - Redirects user back to frontend `/providers` with success status.

---

## 3. Microsoft OneDrive (Microsoft Identity Platform)

### 3.1 Azure Portal Setup
1. Go to the [Azure Portal - App Registrations](https://portal.azure.com/#blade/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/RegisteredApps).
2. Register a new application:
   - Name: `Universal-AI-File-Manager`
   - Supported account types: *Accounts in any organizational directory and personal Microsoft accounts* (Multi-tenant + personal).
   - Redirect URI (Web): `http://localhost:8000/api/providers/onedrive/callback`
3. Under **Certificates & Secrets**, generate a new Client Secret.
4. Under **API Permissions**, add Microsoft Graph delegated permissions:
   - `Files.Read.All`
   - `offline_access`
   - `User.Read`
5. Configure `.env`:
   ```env
   MICROSOFT_CLIENT_ID=your_client_id
   MICROSOFT_CLIENT_SECRET=your_client_secret
   MICROSOFT_TENANT_ID=common
   MICROSOFT_REDIRECT_URI=http://localhost:8000/api/providers/onedrive/callback
   ```

### 3.2 OneDrive OAuth Flow
1. **Initiate**: `GET /api/providers/onedrive/connect`
   - Redirects to `https://login.microsoftonline.com/common/oauth2/v2.0/authorize`.
2. **Callback**: `GET /api/providers/onedrive/callback?code=...&state=...`
   - Validates state.
   - Exchanges code via `https://login.microsoftonline.com/common/oauth2/v2.0/token`.
   - Stores encrypted tokens in `ProviderConnection`.

---

## 4. Dropbox (Dropbox Platform)

### 4.1 Dropbox App Console Setup
1. Go to the [Dropbox App Console](https://www.dropbox.com/developers/apps).
2. Click **Create app**:
   - Choose **Scoped access**.
   - Choose **Full Dropbox** (or App folder if preferred).
3. Under **Permissions**, select:
   - `files.metadata.read`
   - `files.content.read`
   - `account_info.read`
4. Under **Settings**, add Redirect URI:
   - `http://localhost:8000/api/providers/dropbox/callback`
5. Configure `.env`:
   ```env
   DROPBOX_APP_KEY=your_app_key
   DROPBOX_APP_SECRET=your_app_secret
   DROPBOX_REDIRECT_URI=http://localhost:8000/api/providers/dropbox/callback
   ```

### 4.2 Dropbox OAuth Flow
1. **Initiate**: `GET /api/providers/dropbox/connect`
   - Redirects to `https://www.dropbox.com/oauth2/authorize?token_access_type=offline`.
2. **Callback**: `GET /api/providers/dropbox/callback?code=...&state=...`
   - Exchanges code for short-lived access token and refresh token via `https://api.dropboxapi.com/oauth2/token`.
   - Stores encrypted tokens.
