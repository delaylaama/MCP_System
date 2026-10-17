// ============================================================
// Mock Data - Replace these functions with real API calls later
// e.g., searchFiles(query) → fetch('/api/search?q=' + query)
// ============================================================

export const PROVIDERS = {
  GOOGLE_DRIVE: 'Google Drive',
  ONEDRIVE: 'OneDrive',
  DROPBOX: 'Dropbox',
  LOCAL: 'Local',
};

export const FILE_TYPES = {
  pdf: { label: 'PDF', color: '#e53935', icon: 'bi-file-earmark-pdf' },
  docx: { label: 'DOCX', color: '#1565c0', icon: 'bi-file-earmark-word' },
  xlsx: { label: 'XLSX', color: '#2e7d32', icon: 'bi-file-earmark-excel' },
  pptx: { label: 'PPTX', color: '#e65100', icon: 'bi-file-earmark-ppt' },
  jpg: { label: 'JPG', color: '#6a1b9a', icon: 'bi-file-earmark-image' },
  png: { label: 'PNG', color: '#6a1b9a', icon: 'bi-file-earmark-image' },
  txt: { label: 'TXT', color: '#546e7a', icon: 'bi-file-earmark-text' },
  zip: { label: 'ZIP', color: '#795548', icon: 'bi-file-earmark-zip' },
  mp4: { label: 'MP4', color: '#1a237e', icon: 'bi-file-earmark-play' },
  csv: { label: 'CSV', color: '#00695c', icon: 'bi-file-earmark-spreadsheet' },
};

export const mockFiles = [
  {
    id: 1,
    name: 'Appointment_Letter_2026.txt',
    provider: PROVIDERS.LOCAL,
    type: 'txt',
    size: '899 B',
    modified: 'October 15, 2026',
    created: 'October 15, 2026',
    path: 'Local / local_storage',
    favorite: false,
    lastOpened: 'October 16, 2026',
    tags: ['appointment', 'career', 'offer'],
    aiSummary:
      'Official Appointment Letter for Software Engineer 2026 position detailing role, compensation, and joining requirements.',
  },
  {
    id: 2,
    name: 'Final_Year_Project_Report.md',
    provider: PROVIDERS.LOCAL,
    type: 'md',
    size: '992 B',
    modified: 'October 15, 2026',
    created: 'October 15, 2026',
    path: 'Local / local_storage',
    favorite: true,
    lastOpened: 'October 16, 2026',
    tags: ['project', 'mcp', 'final-year', 'report'],
    aiSummary:
      'Comprehensive Final Year Project Report on the Universal AI File Manager using Model Context Protocol (MCP) architecture.',
  },
  {
    id: 3,
    name: 'June_Invoice_Cloud_2026.txt',
    provider: PROVIDERS.LOCAL,
    type: 'txt',
    size: '1.0 KB',
    modified: 'October 15, 2026',
    created: 'October 15, 2026',
    path: 'Local / local_storage',
    favorite: false,
    lastOpened: 'October 16, 2026',
    tags: ['invoice', 'finance', 'cloud', 'june'],
    aiSummary:
      'Cloud infrastructure invoice for June 2026 covering storage and compute services.',
  },
  {
    id: 4,
    name: 'Resume_Computer_Science_2026.md',
    provider: PROVIDERS.LOCAL,
    type: 'md',
    size: '1.2 KB',
    modified: 'October 15, 2026',
    created: 'October 15, 2026',
    path: 'Local / local_storage',
    favorite: true,
    lastOpened: 'October 16, 2026',
    tags: ['resume', 'career', 'computer-science'],
    aiSummary:
      'Updated 2026 Computer Science Resume highlighting AI engineering, full-stack development, and MCP projects.',
  },
];

export const mockStorageProviders = [
  {
    id: 'google_drive',
    name: 'Google Drive',
    connected: false,
    fileCount: 0,
    usedStorage: '0 B',
    totalStorage: '15 GB',
    usedPercent: 0,
    lastSync: '—',
    description: 'Search and manage files stored in your Google Drive account.',
    permissions: ['Read files', 'Search files', 'Read file metadata'],
  },
  {
    id: 'onedrive',
    name: 'OneDrive',
    connected: false,
    fileCount: 0,
    usedStorage: '0 B',
    totalStorage: '5 GB',
    usedPercent: 0,
    lastSync: '—',
    description: 'Access your Microsoft OneDrive files through the AI assistant.',
    permissions: ['Read files', 'Search files', 'Read file metadata'],
  },
  {
    id: 'dropbox',
    name: 'Dropbox',
    connected: false,
    fileCount: 0,
    usedStorage: '0 B',
    totalStorage: '2 GB',
    usedPercent: 0,
    lastSync: '—',
    description: 'Connect your Dropbox to search files with AI assistance.',
    permissions: ['Read files', 'Search files', 'Read file metadata'],
  },
  {
    id: 'local',
    name: 'Local Storage',
    connected: true,
    fileCount: 4,
    usedStorage: '4 KB',
    totalStorage: '550.0 GB',
    usedPercent: 0.1,
    lastSync: 'Just now',
    description: 'Index and search files from your local file system.',
    permissions: ['Read files', 'Search files', 'Read file metadata'],
  },
];

export const mockAIResponses = [
  {
    query: 'find my latest resume',
    results: [4],
    message:
      'I found your Computer Science resume (Resume_Computer_Science_2026.md) in your local storage.',
  },
  {
    query: 'show project reports',
    results: [2],
    message:
      'I found your Final Year Project Report (Final_Year_Project_Report.md) on the Universal AI File Manager in your local storage.',
  },
  {
    query: 'show invoices from june',
    results: [3],
    message:
      'I found your June Cloud invoice (June_Invoice_Cloud_2026.txt) in your local storage.',
  },
  {
    query: 'find appointment letter',
    results: [1],
    message:
      'I found your official Appointment Letter (Appointment_Letter_2026.txt) in your local storage.',
  },
];

// ============================================================
// Service functions — replace with real API calls later
// ============================================================

/**
 * Searches files by query string
 * Later: return fetch('/api/search?q=' + encodeURIComponent(query)).then(r => r.json())
 */
export async function searchFiles(query) {
  await new Promise((resolve) => setTimeout(resolve, 1200)); // simulate network delay

  if (!query.trim()) return { files: [], message: 'Please enter a search query.' };

  const lowerQuery = query.toLowerCase();

  // Check for predefined AI responses
  const aiResponse = mockAIResponses.find((r) =>
    lowerQuery.includes(r.query.split(' ')[1]) ||
    r.query.toLowerCase().includes(lowerQuery.split(' ')[1] || lowerQuery)
  );

  if (aiResponse) {
    return {
      files: mockFiles.filter((f) => aiResponse.results.includes(f.id)),
      message: aiResponse.message,
    };
  }

  // Generic keyword search
  const results = mockFiles.filter(
    (f) =>
      f.name.toLowerCase().includes(lowerQuery) ||
      f.tags.some((t) => t.includes(lowerQuery)) ||
      f.provider.toLowerCase().includes(lowerQuery) ||
      f.type.toLowerCase().includes(lowerQuery)
  );

  if (results.length === 0) {
    return { files: [], message: `No files found matching "${query}". Try a different search term.` };
  }

  return {
    files: results,
    message: `I found ${results.length} file${results.length > 1 ? 's' : ''} matching "${query}" across your connected storage providers.`,
  };
}

/**
 * Gets all files with optional filtering/sorting
 * Later: return fetch('/api/files?provider=' + provider + '&sort=' + sort).then(r => r.json())
 */
export async function getFiles({ provider = 'all', sort = 'latest', search = '' } = {}) {
  await new Promise((resolve) => setTimeout(resolve, 400));

  let files = [...mockFiles];

  if (provider !== 'all') {
    files = files.filter((f) => f.provider === provider);
  }

  if (search) {
    const q = search.toLowerCase();
    files = files.filter(
      (f) =>
        f.name.toLowerCase().includes(q) ||
        f.tags.some((t) => t.includes(q))
    );
  }

  switch (sort) {
    case 'oldest':
      files = files.sort((a, b) => a.id - b.id);
      break;
    case 'name-asc':
      files = files.sort((a, b) => a.name.localeCompare(b.name));
      break;
    case 'name-desc':
      files = files.sort((a, b) => b.name.localeCompare(a.name));
      break;
    case 'size':
      files = files.sort((a, b) => parseFloat(b.size) - parseFloat(a.size));
      break;
    default: // latest
      files = files.sort((a, b) => b.id - a.id);
  }

  return files;
}

/**
 * Gets a single file by id
 * Later: return fetch('/api/files/' + id).then(r => r.json())
 */
export async function getFileById(id) {
  await new Promise((resolve) => setTimeout(resolve, 300));
  return mockFiles.find((f) => f.id === parseInt(id)) || null;
}

/**
 * Gets recent files
 * Later: return fetch('/api/files/recent').then(r => r.json())
 */
export async function getRecentFiles() {
  await new Promise((resolve) => setTimeout(resolve, 400));
  return [...mockFiles].sort((a, b) => b.id - a.id).slice(0, 10);
}

/**
 * Gets favorite files
 * Later: return fetch('/api/files/favorites').then(r => r.json())
 */
export async function getFavoriteFiles() {
  await new Promise((resolve) => setTimeout(resolve, 300));
  return mockFiles.filter((f) => f.favorite);
}

/**
 * Toggles favorite status
 * Later: return fetch('/api/files/' + id + '/favorite', { method: 'POST' })
 */
export async function toggleFavorite(id) {
  await new Promise((resolve) => setTimeout(resolve, 200));
  const file = mockFiles.find((f) => f.id === id);
  if (file) file.favorite = !file.favorite;
  return file;
}

/**
 * Gets storage provider statuses
 * Later: return fetch('/api/storage/providers').then(r => r.json())
 */
export async function getStorageProviders() {
  await new Promise((resolve) => setTimeout(resolve, 300));
  return [...mockStorageProviders];
}

/**
 * Mock authentication
 * Later: return fetch('/api/auth/login', { method: 'POST', body: JSON.stringify(creds) })
 */
export async function loginUser({ email, password }) {
  await new Promise((resolve) => setTimeout(resolve, 800));
  if (email && password.length >= 6) {
    return {
      success: true,
      user: {
        name: 'Meens',
        fullName: 'Meenatchi Sundaram',
        email,
        avatar: null,
      },
    };
  }
  return { success: false, error: 'Invalid email or password.' };
}

/**
 * Mock registration
 * Later: return fetch('/api/auth/register', { method: 'POST', body: JSON.stringify(data) })
 */
export async function registerUser({ name, email, password }) {
  await new Promise((resolve) => setTimeout(resolve, 800));
  if (name && email && password.length >= 6) {
    return { success: true };
  }
  return { success: false, error: 'Registration failed. Please check your details.' };
}
