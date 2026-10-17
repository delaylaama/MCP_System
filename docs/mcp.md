# Model Context Protocol (MCP) Architecture & Tools

This document defines how Universal AI File Manager utilizes the **Model Context Protocol (MCP)** Python SDK v2.

---

## 1. Why MCP?

In traditional multi-cloud architectures, each new cloud provider introduces tight coupling:
- The LLM prompt engineering must be rewritten for each cloud vendor's unique query grammar.
- Authentication, pagination, and error responses leak into the business logic.
- Adding a new provider requires updating frontend, backend services, and AI agent prompts.

MCP standardizes tool declarations and tool invocations into an open, vendor-neutral protocol:
```
           +-------------------------------------+
           |           FastAPI Backend           |
           |             (AI Service)            |
           +------------------+------------------+
                              |
                     MCP Client (Async)
                              |  Streamable HTTP / SSE
                     MCP Server (:8001/mcp)
                              |
       +----------------------+----------------------+
       |                      |                      |
search_files()           list_files()        get_file_content()
       |                      |                      |
       +----------------------+----------------------+
                              |
                       ProviderManager
                              |
       +------------+---------+---------+------------+
       |            |                   |            |
 Google Drive   OneDrive             Dropbox       Local
```

---

## 2. MCP Tools Specification

### 2.1 `search_files`
Searches connected cloud and local providers matching a query string and optional filters.
- **Input Schema**:
  - `query` (str): Search keywords or semantic prompt.
  - `provider` (str, optional): Target provider (`google_drive`, `onedrive`, `dropbox`, `local`, or `all`).
  - `file_type` (str, optional): Target extension or category (e.g. `pdf`, `image`, `document`).
  - `modified_after` (str, optional): ISO-8601 timestamp filter.
  - `modified_before` (str, optional): ISO-8601 timestamp filter.
  - `user_id` (str, optional): Scoped user context.
- **Output**: Array of `FileRecord` objects.

### 2.2 `list_files`
Lists files and folders within a specific folder or root directory.
- **Input Schema**:
  - `provider` (str, optional): Target provider.
  - `folder_id` (str, optional): Cloud folder ID or local path.
  - `limit` (int, default 50): Maximum items to return.
- **Output**: Array of `FileRecord` objects.

### 2.3 `get_file_metadata`
Fetches full standardized metadata for a specific provider file ID.
- **Input Schema**:
  - `file_id` (str): Unique file identifier within the provider.
  - `provider` (str): Storage provider.
- **Output**: Single `FileRecord` object.

### 2.4 `get_file_content`
Extracts text content for document summarization or semantic processing.
- **Input Schema**:
  - `file_id` (str): Provider file ID.
  - `provider` (str): Storage provider.
  - `max_bytes` (int, default 1,048,576): Maximum bytes to read.
- **Output**: Textual representation or extracted text from document.

### 2.5 `download_file`
Retrieves binary download stream metadata and chunked bytes.

### 2.6 `find_duplicates`
Cross-analyzes files across all connected storage providers and returns duplicate clusters based on SHA-256 hashes and metadata.
