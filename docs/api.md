# REST API Reference

Universal AI File Manager exposes a clean RESTful API under the `/api` prefix.

---

## 1. Authentication Endpoints

### `POST /api/auth/register`
Creates a new user account.
- **Request Body**:
  ```json
  {
    "email": "student@university.edu",
    "password": "SecurePassword123!",
    "full_name": "Final Year Student"
  }
  ```
- **Response `201 Created`**:
  ```json
  {
    "id": "c1f7b764-508b-4a55-b44c-22361df4ebfa",
    "email": "student@university.edu",
    "full_name": "Final Year Student",
    "created_at": "2026-09-24T18:00:00Z"
  }
  ```

### `POST /api/auth/login`
Authenticates a user and issues a JWT Bearer token.
- **Request Body**:
  ```json
  {
    "username": "student@university.edu",
    "password": "SecurePassword123!"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": "c1f7b764-508b-4a55-b44c-22361df4ebfa",
      "email": "student@university.edu",
      "full_name": "Final Year Student"
    }
  }
  ```

### `GET /api/auth/me`
Retrieves current authenticated user profile.
- **Headers**: `Authorization: Bearer <token>`
- **Response `200 OK`**

---

## 2. Storage Providers Endpoints

### `GET /api/providers`
Lists all supported storage providers along with the user's connection status.
- **Response `200 OK`**:
  ```json
  [
    {
      "provider": "google_drive",
      "name": "Google Drive",
      "connected": true,
      "account_identifier": "student@gmail.com",
      "connected_at": "2026-09-20T12:00:00Z"
    },
    {
      "provider": "onedrive",
      "name": "Microsoft OneDrive",
      "connected": false,
      "account_identifier": null,
      "connected_at": null
    },
    {
      "provider": "dropbox",
      "name": "Dropbox",
      "connected": false,
      "account_identifier": null,
      "connected_at": null
    },
    {
      "provider": "local",
      "name": "Local Storage",
      "connected": true,
      "account_identifier": "./local_storage",
      "connected_at": "2026-09-24T00:00:00Z"
    }
  ]
  ```

### `GET /api/providers/{provider}/connect`
Generates the OAuth consent URL and initiates the provider handshake.

### `GET /api/providers/{provider}/callback`
OAuth 2.0 redirect receiver that exchanges authorization codes for tokens.

### `DELETE /api/providers/{provider}`
Disconnects a provider and purges associated credentials and cached tokens.

---

## 3. Search Endpoints

### `POST /api/search`
Executes natural-language AI search or structured keyword/semantic search.
- **Request Body**:
  ```json
  {
    "query": "Find the latest invoice from June",
    "providers": ["google_drive", "local"],
    "file_type": "pdf",
    "use_ai": true,
    "limit": 20
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "query": "Find the latest invoice from June",
    "interpreted_intent": {
      "action": "search_files",
      "parameters": {
        "query": "invoice",
        "modified_after": "2026-06-01T00:00:00Z",
        "modified_before": "2026-06-30T23:59:59Z"
      }
    },
    "ai_summary": "I retrieved 2 invoice documents from June 2026 across your connected Google Drive and Local Storage.",
    "total_results": 2,
    "results": [
      {
        "id": "rec_01",
        "name": "June_Invoice_2026.pdf",
        "provider": "google_drive",
        "provider_file_id": "1A2B3C4D",
        "path": "/Finance/June_Invoice_2026.pdf",
        "mime_type": "application/pdf",
        "extension": ".pdf",
        "size": 142050,
        "modified_at": "2026-06-28T14:32:00Z",
        "web_url": "https://drive.google.com/file/d/1A2B3C4D/view",
        "downloadable": true,
        "score": 0.94,
        "score_breakdown": {
          "keyword_score": 0.95,
          "semantic_score": 0.92,
          "recency_score": 0.96
        }
      }
    ]
  }
  ```

### `GET /api/search/history`
Returns historical queries submitted by the authenticated user.

### `DELETE /api/search/history`
Clears search history for the user.

---

## 4. File Management Endpoints

### `GET /api/files/{id}`
Returns unified metadata for a specific file.

### `GET /api/files/{id}/download`
Streams the binary content of the file from its cloud provider.

### `GET /api/files/duplicates`
Returns groups of identical files detected across distinct storage providers.
