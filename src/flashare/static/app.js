/**
 * Flashare - Mobile Web Application
 * Handles file listing, downloads, uploads, and Web Bluetooth scanning
 */

// ==================== Constants ====================
const API = {
  files: "/api/files",
  download: (name, compressed = true) => `/api/download/${encodeURIComponent(name)}?compressed=${compressed}`,
  upload: "/api/upload",
  status: "/api/status",
  qr: "/api/qr",
}

// ==================== State ====================
let files = []
let isUploading = false

// ==================== DOM Elements ====================
const elements = {
  fileList: document.getElementById("fileList"),
  fileCount: document.getElementById("fileCount"),
  serverUrl: document.getElementById("serverUrl"),
  statusCard: document.getElementById("statusCard"),
  refreshBtn: document.getElementById("refreshBtn"),
  uploadBtn: document.getElementById("uploadBtn"),
  uploadModal: document.getElementById("uploadModal"),
  uploadArea: document.getElementById("uploadArea"),
  fileInput: document.getElementById("fileInput"),
  hiddenFileInput: document.getElementById("hiddenFileInput"),
  uploadProgress: document.getElementById("uploadProgress"),
  progressFill: document.getElementById("progressFill"),
  progressText: document.getElementById("progressText"),
  cancelUploadBtn: document.getElementById("cancelUploadBtn"),
  toastContainer: document.getElementById("toastContainer"),
}

// ==================== File Icons ====================
const FILE_ICONS = {
  // Images
  jpg: "🖼️",
  jpeg: "🖼️",
  png: "🖼️",
  gif: "🖼️",
  webp: "🖼️",
  svg: "🖼️",
  // Videos
  mp4: "🎬",
  mov: "🎬",
  avi: "🎬",
  mkv: "🎬",
  webm: "🎬",
  // Audio
  mp3: "🎵",
  wav: "🎵",
  flac: "🎵",
  aac: "🎵",
  ogg: "🎵",
  // Documents
  pdf: "📄",
  doc: "📝",
  docx: "📝",
  txt: "📝",
  rtf: "📝",
  // Spreadsheets
  xls: "📊",
  xlsx: "📊",
  csv: "📊",
  // Archives
  zip: "📦",
  rar: "📦",
  "7z": "📦",
  tar: "📦",
  gz: "📦",
  // Code
  js: "💻",
  py: "💻",
  html: "💻",
  css: "💻",
  json: "💻",
  // Default
  default: "📁",
}

function getFileIcon(filename) {
  const ext = filename.split(".").pop()?.toLowerCase() || ""
  return FILE_ICONS[ext] || FILE_ICONS.default
}

// ==================== API Functions ====================
async function fetchFiles() {
  try {
    const response = await fetch(API.files)
    if (!response.ok) throw new Error("Failed to fetch files")
    return await response.json()
  } catch (error) {
    console.error("Error fetching files:", error)
    throw error
  }
}

async function fetchStatus() {
  try {
    const response = await fetch(API.status)
    if (!response.ok) throw new Error("Failed to fetch status")
    return await response.json()
  } catch (error) {
    console.error("Error fetching status:", error)
    throw error
  }
}

async function uploadFile(file, onProgress) {
  const formData = new FormData()
  formData.append("file", file)

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    })

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText))
      } else {
        reject(new Error("Upload failed"))
      }
    })

    xhr.addEventListener("error", () => reject(new Error("Upload failed")))

    xhr.open("POST", API.upload)
    xhr.send(formData)
  })
}

// ==================== UI Functions ====================
function renderFiles() {
  if (files.length === 0) {
    elements.fileList.innerHTML = `
            <div class="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                    <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
                </svg>
                <p>No files available yet</p>
                <p>Share files from your laptop to see them here</p>
            </div>
        `
    elements.fileCount.textContent = "0"
    return
  }

  elements.fileCount.textContent = files.length.toString()
  elements.fileList.innerHTML = files
    .map(
      (file) => `
        <div class="file-card" data-filename="${escapeHtml(file.name)}">
            <div class="file-icon">${getFileIcon(file.name)}</div>
            <div class="file-info">
                <div class="file-name">${escapeHtml(file.name)}</div>
                <div class="file-meta">${file.size_human}</div>
            </div>
            <div class="file-actions">
                <button class="download-btn" data-filename="${escapeHtml(file.name)}" title="Download">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                        <polyline points="7 10 12 15 17 10"/>
                        <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                </button>
            </div>
        </div>
    `,
    )
    .join("")

  // Add download event listeners
  elements.fileList.querySelectorAll(".download-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      const filename = btn.dataset.filename
      downloadFile(filename)
    })
  })
}

function downloadFile(filename) {
  // Create a temporary link and trigger download
  // Using uncompressed for browser compatibility
  const link = document.createElement("a")
  link.href = API.download(filename, false)
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  showToast(`Downloading ${filename}`, "success")
}

function showLoading() {
  elements.fileList.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <span>Loading files...</span>
        </div>
    `
}

function showToast(message, type = "info") {
  const icons = {
    success: "✓",
    error: "✕",
    warning: "⚠",
    info: "ℹ",
  }

  const toast = document.createElement("div")
  toast.className = `toast ${type}`
  toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <span class="toast-message">${escapeHtml(message)}</span>
    `

  elements.toastContainer.appendChild(toast)

  // Auto-remove after 3 seconds
  setTimeout(() => {
    toast.style.opacity = "0"
    toast.style.transform = "translateY(10px)"
    setTimeout(() => toast.remove(), 300)
  }, 3000)
}

function escapeHtml(text) {
  const div = document.createElement("div")
  div.textContent = text
  return div.innerHTML
}

// ==================== Modal Functions ====================
function openUploadModal() {
  elements.uploadModal.classList.add("active")
  elements.uploadProgress.hidden = true
  elements.uploadArea.style.display = "flex"
}

function closeUploadModal() {
  elements.uploadModal.classList.remove("active")
}

// ==================== Event Handlers ====================
async function handleRefresh() {
  showLoading()
  try {
    files = await fetchFiles()
    renderFiles()
    showToast("Files refreshed", "success")
  } catch (error) {
    showToast("Failed to load files", "error")
    elements.fileList.innerHTML = `
            <div class="empty-state">
                <p>Failed to load files</p>
                <p>Check your connection and try again</p>
            </div>
        `
  }
}

async function handleUpload(file) {
  if (isUploading) return

  isUploading = true
  elements.uploadArea.style.display = "none"
  elements.uploadProgress.hidden = false
  elements.progressFill.style.width = "0%"
  elements.progressText.textContent = "0%"

  try {
    await uploadFile(file, (progress) => {
      elements.progressFill.style.width = `${progress}%`
      elements.progressText.textContent = `${progress}%`
    })

    showToast(`Uploaded: ${file.name}`, "success")
    closeUploadModal()
    await handleRefresh()
  } catch (error) {
    showToast("Upload failed", "error")
    elements.uploadArea.style.display = "flex"
    elements.uploadProgress.hidden = true
  }

  isUploading = false
}

// ==================== Initialization ====================
async function init() {
  // Load initial data
  try {
    const [filesData, status] = await Promise.all([fetchFiles(), fetchStatus()])

    files = filesData
    elements.serverUrl.textContent = status.url
    renderFiles()
  } catch (error) {
    console.error("Initialization error:", error)
    elements.serverUrl.textContent = window.location.origin
    elements.fileList.innerHTML = `
            <div class="empty-state">
                <p>Failed to connect</p>
                <p>Please refresh the page</p>
            </div>
        `
  }

  // Event Listeners
  elements.refreshBtn.addEventListener("click", handleRefresh)
  elements.uploadBtn.addEventListener("click", openUploadModal)
  elements.cancelUploadBtn.addEventListener("click", closeUploadModal)

  // Upload modal backdrop click
  elements.uploadModal.querySelector(".modal-backdrop").addEventListener("click", closeUploadModal)

  // Upload area click
  elements.uploadArea.addEventListener("click", () => {
    elements.hiddenFileInput.click()
  })

  // File input change
  elements.hiddenFileInput.addEventListener("change", (e) => {
    const file = e.target.files?.[0]
    if (file) {
      handleUpload(file)
    }
  })

  // Drag and drop
  elements.uploadArea.addEventListener("dragover", (e) => {
    e.preventDefault()
    elements.uploadArea.classList.add("dragover")
  })

  elements.uploadArea.addEventListener("dragleave", () => {
    elements.uploadArea.classList.remove("dragover")
  })

  elements.uploadArea.addEventListener("drop", (e) => {
    e.preventDefault()
    elements.uploadArea.classList.remove("dragover")
    const file = e.dataTransfer?.files?.[0]
    if (file) {
      handleUpload(file)
    }
  })

  // Auto-refresh every 30 seconds
  setInterval(async () => {
    try {
      files = await fetchFiles()
      renderFiles()
    } catch (error) {
      // Silent fail for auto-refresh
    }
  }, 30000)
}

// Start the app
document.addEventListener("DOMContentLoaded", init)
