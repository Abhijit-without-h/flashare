/**
 * Flashare - Mobile Web Application
 * Enhanced with Multi-File Upload, Parallel Processing & Performance Optimizations
 */

// ==================== Constants ====================
const API = {
  files: "/api/files",
  download: (name, compressed = true) => `/api/download/${encodeURIComponent(name)}?compressed=${compressed}`,
  upload: "/api/upload",
  uploadMultiple: "/api/upload-multiple",
  delete: (name) => `/api/files/${encodeURIComponent(name)}`,
  status: "/api/status",
  qr: "/api/qr",
}

const MAX_CONCURRENT_UPLOADS = 3
const THUMBNAIL_SIZE = 80
const CHUNK_SIZE = 1024 * 1024 // 1MB chunks for large file reading

// ==================== State ====================
let files = []
let uploadQueue = []
let uploadProgress = new Map()
let isUploading = false
let selectedFiles = new Set()
let isSelectMode = false
let abortControllers = new Map()
let isDarkTheme = true

// ==================== DOM Elements (Lazy Load Pattern) ====================
const getElements = (() => {
  let cached = null
  return () => {
    if (!cached) {
      cached = {
        fileList: document.getElementById("fileList"),
        fileCount: document.getElementById("fileCount"),
        serverUrl: document.getElementById("serverUrl"),
        statusCard: document.getElementById("statusCard"),
        refreshBtn: document.getElementById("refreshBtn"),
        uploadBtn: document.getElementById("uploadBtn"),
        uploadBadge: document.getElementById("uploadBadge"),
        uploadModal: document.getElementById("uploadModal"),
        uploadArea: document.getElementById("uploadArea"),
        hiddenFileInput: document.getElementById("hiddenFileInput"),
        fileQueue: document.getElementById("fileQueue"),
        queueList: document.getElementById("queueList"),
        queueCount: document.getElementById("queueCount"),
        queueSize: document.getElementById("queueSize"),
        clearQueueBtn: document.getElementById("clearQueueBtn"),
        startUploadBtn: document.getElementById("startUploadBtn"),
        uploadProgressContainer: document.getElementById("uploadProgressContainer"),
        progressList: document.getElementById("progressList"),
        progressStats: document.getElementById("progressStats"),
        overallProgressFill: document.getElementById("overallProgressFill"),
        cancelUploadBtn: document.getElementById("cancelUploadBtn"),
        closeModalBtn: document.getElementById("closeModalBtn"),
        toastContainer: document.getElementById("toastContainer"),
        selectModeBtn: document.getElementById("selectModeBtn"),
        batchActions: document.getElementById("batchActions"),
        selectAllBtn: document.getElementById("selectAllBtn"),
        downloadSelectedBtn: document.getElementById("downloadSelectedBtn"),
        deleteSelectedBtn: document.getElementById("deleteSelectedBtn"),
        themeToggle: document.getElementById("themeToggle"),
        mobileCapture: document.getElementById("mobileCapture"),
        capturePhotoBtn: document.getElementById("capturePhotoBtn"),
        captureGalleryBtn: document.getElementById("captureGalleryBtn"),
        cameraInput: document.getElementById("cameraInput"),
        galleryInput: document.getElementById("galleryInput"),
      }
    }
    return cached
  }
})()

// ==================== File Icons (Optimized Map) ====================
const FILE_ICONS = new Map([
  // Images
  ["jpg", "🖼️"], ["jpeg", "🖼️"], ["png", "🖼️"], ["gif", "🖼️"], ["webp", "🖼️"], ["svg", "🖼️"], ["heic", "🖼️"],
  // Videos
  ["mp4", "🎬"], ["mov", "🎬"], ["avi", "🎬"], ["mkv", "🎬"], ["webm", "🎬"], ["m4v", "🎬"],
  // Audio
  ["mp3", "🎵"], ["wav", "🎵"], ["flac", "🎵"], ["aac", "🎵"], ["ogg", "🎵"], ["m4a", "🎵"],
  // Documents
  ["pdf", "📄"], ["doc", "📝"], ["docx", "📝"], ["txt", "📝"], ["rtf", "📝"], ["md", "📝"],
  // Spreadsheets
  ["xls", "📊"], ["xlsx", "📊"], ["csv", "📊"],
  // Archives
  ["zip", "📦"], ["rar", "📦"], ["7z", "📦"], ["tar", "📦"], ["gz", "📦"],
  // Code
  ["js", "💻"], ["py", "💻"], ["html", "💻"], ["css", "💻"], ["json", "💻"], ["ts", "💻"],
])

const getFileIcon = (filename) => {
  const ext = filename.split(".").pop()?.toLowerCase() || ""
  return FILE_ICONS.get(ext) || "📁"
}

// ==================== Utility Functions (Lambda-Style) ====================
const formatSize = (bytes) => {
  const units = ["B", "KB", "MB", "GB", "TB"]
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024
    i++
  }
  return `${bytes.toFixed(1)} ${units[i]}`
}

const escapeHtml = (text) => {
  const div = document.createElement("div")
  div.textContent = text
  return div.innerHTML
}

const debounce = (fn, delay) => {
  let timeout
  return (...args) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => fn(...args), delay)
  }
}

const throttle = (fn, limit) => {
  let inThrottle
  return (...args) => {
    if (!inThrottle) {
      fn(...args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

// Parallel processing helper with concurrency limit
const parallelLimit = async (tasks, limit) => {
  const results = []
  const executing = new Set()

  for (const [index, task] of tasks.entries()) {
    const promise = Promise.resolve().then(() => task()).then(result => {
      executing.delete(promise)
      return { index, result, success: true }
    }).catch(error => {
      executing.delete(promise)
      return { index, error, success: false }
    })

    results.push(promise)
    executing.add(promise)

    if (executing.size >= limit) {
      await Promise.race(executing)
    }
  }

  return Promise.all(results)
}

// ==================== API Functions ====================
const fetchFiles = async () => {
  const response = await fetch(API.files)
  if (!response.ok) throw new Error("Failed to fetch files")
  return response.json()
}

const fetchStatus = async () => {
  const response = await fetch(API.status)
  if (!response.ok) throw new Error("Failed to fetch status")
  return response.json()
}

const uploadFile = (file, onProgress, abortSignal) => {
  return new Promise((resolve, reject) => {
    const formData = new FormData()
    formData.append("file", file)

    const xhr = new XMLHttpRequest()

    // Store abort handler
    if (abortSignal) {
      abortSignal.addEventListener("abort", () => {
        xhr.abort()
        reject(new Error("Upload cancelled"))
      })
    }

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    })

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText))
      } else {
        reject(new Error(`Upload failed: ${xhr.status}`))
      }
    })

    xhr.addEventListener("error", () => reject(new Error("Upload failed")))
    xhr.addEventListener("abort", () => reject(new Error("Upload cancelled")))

    xhr.open("POST", API.upload)
    xhr.send(formData)
  })
}

const deleteFile = async (filename) => {
  const response = await fetch(API.delete(filename), { method: "DELETE" })
  if (!response.ok) throw new Error("Failed to delete file")
  return response.json()
}

// ==================== Thumbnail Generation (Optimized) ====================
const generateThumbnail = async (file) => {
  return new Promise((resolve) => {
    if (file.type.startsWith("image/")) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const img = new Image()
        img.onload = () => {
          const canvas = document.createElement("canvas")
          const ctx = canvas.getContext("2d")

          // Calculate crop dimensions for square thumbnail
          const size = Math.min(img.width, img.height)
          const x = (img.width - size) / 2
          const y = (img.height - size) / 2

          canvas.width = THUMBNAIL_SIZE
          canvas.height = THUMBNAIL_SIZE
          ctx.drawImage(img, x, y, size, size, 0, 0, THUMBNAIL_SIZE, THUMBNAIL_SIZE)

          resolve(canvas.toDataURL("image/jpeg", 0.7))
        }
        img.onerror = () => resolve(null)
        img.src = e.target.result
      }
      reader.onerror = () => resolve(null)
      reader.readAsDataURL(file.slice(0, 5 * 1024 * 1024)) // Only read first 5MB for thumbnail
    } else if (file.type.startsWith("video/")) {
      const video = document.createElement("video")
      video.preload = "metadata"
      video.muted = true

      video.onloadeddata = () => {
        video.currentTime = Math.min(1, video.duration / 2)
      }

      video.onseeked = () => {
        const canvas = document.createElement("canvas")
        const ctx = canvas.getContext("2d")

        const size = Math.min(video.videoWidth, video.videoHeight)
        const x = (video.videoWidth - size) / 2
        const y = (video.videoHeight - size) / 2

        canvas.width = THUMBNAIL_SIZE
        canvas.height = THUMBNAIL_SIZE
        ctx.drawImage(video, x, y, size, size, 0, 0, THUMBNAIL_SIZE, THUMBNAIL_SIZE)

        URL.revokeObjectURL(video.src)
        resolve(canvas.toDataURL("image/jpeg", 0.7))
      }

      video.onerror = () => {
        URL.revokeObjectURL(video.src)
        resolve(null)
      }

      video.src = URL.createObjectURL(file)
    } else {
      resolve(null)
    }
  })
}

// Batch thumbnail generation with parallel processing
const generateThumbnailsBatch = async (files) => {
  const tasks = files.map((file, index) => async () => {
    const thumbnail = await generateThumbnail(file)
    return { index, thumbnail }
  })

  const results = await parallelLimit(tasks, 4) // Process 4 thumbnails at a time
  const thumbnails = new Array(files.length).fill(null)

  results.forEach(({ result }) => {
    if (result) thumbnails[result.index] = result.thumbnail
  })

  return thumbnails
}

// ==================== Queue Management ====================
const addToQueue = async (fileList) => {
  const elements = getElements()
  const newFiles = Array.from(fileList)

  // Generate thumbnails in parallel
  const thumbnails = await generateThumbnailsBatch(newFiles)

  newFiles.forEach((file, i) => {
    // Check for duplicates
    if (!uploadQueue.some(f => f.name === file.name && f.size === file.size)) {
      uploadQueue.push({
        file,
        id: `${Date.now()}-${i}-${Math.random().toString(36).substr(2, 9)}`,
        thumbnail: thumbnails[i],
        progress: 0,
        status: "pending", // pending, uploading, completed, failed
      })
    }
  })

  renderQueue()
  updateQueueUI()
}

const removeFromQueue = (id) => {
  uploadQueue = uploadQueue.filter(item => item.id !== id)
  renderQueue()
  updateQueueUI()
}

const clearQueue = () => {
  uploadQueue = []
  renderQueue()
  updateQueueUI()
}

const updateQueueUI = () => {
  const elements = getElements()
  const count = uploadQueue.length
  const totalSize = uploadQueue.reduce((sum, item) => sum + item.file.size, 0)

  elements.queueCount.textContent = `${count} file${count !== 1 ? "s" : ""} selected`
  elements.queueSize.textContent = `Total: ${formatSize(totalSize)}`

  elements.fileQueue.hidden = count === 0
  elements.uploadArea.style.display = count > 0 ? "none" : "flex"
  elements.startUploadBtn.disabled = count === 0 || isUploading

  // Update badge
  elements.uploadBadge.textContent = count
  elements.uploadBadge.hidden = count === 0
}

const renderQueue = () => {
  const elements = getElements()

  if (uploadQueue.length === 0) {
    elements.queueList.innerHTML = ""
    return
  }

  elements.queueList.innerHTML = uploadQueue.map(item => `
    <div class="queue-item" data-id="${item.id}">
      <div class="queue-item-preview">
        ${item.thumbnail
      ? `<img src="${item.thumbnail}" alt="preview" loading="lazy">`
      : `<span class="queue-item-icon">${getFileIcon(item.file.name)}</span>`
    }
      </div>
      <div class="queue-item-info">
        <span class="queue-item-name">${escapeHtml(item.file.name)}</span>
        <span class="queue-item-size">${formatSize(item.file.size)}</span>
      </div>
      <button class="queue-item-remove" data-id="${item.id}" title="Remove">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
  `).join("")

  // Add remove handlers using event delegation
  elements.queueList.querySelectorAll(".queue-item-remove").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      removeFromQueue(btn.dataset.id)
    })
  })
}

// ==================== Multi-File Upload with Parallel Processing ====================
const uploadAllFiles = async () => {
  if (isUploading || uploadQueue.length === 0) return

  const elements = getElements()
  isUploading = true

  // Show progress UI
  elements.uploadArea.style.display = "none"
  elements.fileQueue.hidden = true
  elements.uploadProgressContainer.hidden = false
  elements.startUploadBtn.disabled = true
  elements.cancelUploadBtn.textContent = "Cancel All"

  // Reset progress
  uploadProgress.clear()
  abortControllers.clear()

  let completed = 0
  let failed = 0
  const total = uploadQueue.length

  // Render initial progress list
  renderProgressList()
  updateOverallProgress(0, total)

  // Create upload tasks
  const uploadTasks = uploadQueue.map((item, index) => async () => {
    const controller = new AbortController()
    abortControllers.set(item.id, controller)

    try {
      item.status = "uploading"
      renderProgressItem(item)

      await uploadFile(
        item.file,
        (progress) => {
          item.progress = progress
          renderProgressItem(item)
          updateOverallProgress(completed, total)
        },
        controller.signal
      )

      item.status = "completed"
      item.progress = 100
      completed++
      renderProgressItem(item)
      updateOverallProgress(completed, total)

      return { success: true, item }
    } catch (error) {
      if (error.message !== "Upload cancelled") {
        item.status = "failed"
        item.error = error.message
        failed++
        renderProgressItem(item)
      }
      return { success: false, item, error }
    }
  })

  // Execute uploads with parallel limit
  await parallelLimit(uploadTasks, MAX_CONCURRENT_UPLOADS)

  // Upload complete
  isUploading = false
  abortControllers.clear()

  // Show results
  if (failed === 0) {
    showToast(`Successfully uploaded ${completed} file${completed !== 1 ? "s" : ""}`, "success")
    setTimeout(() => {
      closeUploadModal()
      handleRefresh()
    }, 1000)
  } else {
    showToast(`Uploaded ${completed} of ${total} files. ${failed} failed.`, "warning")
  }

  // Reset queue for successful uploads
  uploadQueue = uploadQueue.filter(item => item.status === "failed")
  elements.startUploadBtn.textContent = uploadQueue.length > 0 ? "Retry Failed" : "Upload All"
  elements.startUploadBtn.disabled = uploadQueue.length === 0
  elements.cancelUploadBtn.textContent = "Close"
}

const renderProgressList = () => {
  const elements = getElements()
  elements.progressList.innerHTML = uploadQueue.map(item => `
    <div class="progress-item" data-id="${item.id}">
      <div class="progress-item-info">
        <span class="progress-item-icon">${getFileIcon(item.file.name)}</span>
        <span class="progress-item-name">${escapeHtml(item.file.name)}</span>
        <span class="progress-item-status" data-status="${item.status}">${getStatusText(item)}</span>
      </div>
      <div class="progress-bar small">
        <div class="progress-fill" style="width: ${item.progress}%"></div>
      </div>
    </div>
  `).join("")
}

const renderProgressItem = (item) => {
  const element = document.querySelector(`.progress-item[data-id="${item.id}"]`)
  if (!element) return

  const statusEl = element.querySelector(".progress-item-status")
  const fillEl = element.querySelector(".progress-fill")

  statusEl.dataset.status = item.status
  statusEl.textContent = getStatusText(item)
  fillEl.style.width = `${item.progress}%`

  // Add completed/failed class
  element.classList.remove("completed", "failed", "uploading")
  element.classList.add(item.status)
}

const getStatusText = (item) => {
  switch (item.status) {
    case "pending": return "Waiting..."
    case "uploading": return `${item.progress}%`
    case "completed": return "✓ Done"
    case "failed": return "✕ Failed"
    default: return ""
  }
}

const updateOverallProgress = (completed, total) => {
  const elements = getElements()
  const totalProgress = uploadQueue.reduce((sum, item) => sum + item.progress, 0)
  const overallPercent = Math.round(totalProgress / (total * 100) * 100)

  elements.overallProgressFill.style.width = `${overallPercent}%`
  elements.progressStats.textContent = `${completed} / ${total} completed`
}

const cancelAllUploads = () => {
  abortControllers.forEach(controller => controller.abort())
  abortControllers.clear()
  isUploading = false

  uploadQueue.forEach(item => {
    if (item.status === "uploading") {
      item.status = "pending"
      item.progress = 0
    }
  })
}

// ==================== UI Functions ====================
const renderFiles = () => {
  const elements = getElements()

  if (files.length === 0) {
    elements.fileList.innerHTML = `
      <div class="empty-state">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
        </svg>
        <p>No files available yet</p>
        <p>Upload files to share them across devices</p>
      </div>
    `
    elements.fileCount.textContent = "0"
    return
  }

  elements.fileCount.textContent = files.length.toString()
  elements.fileList.innerHTML = files.map((file, index) => `
    <div class="file-card ${selectedFiles.has(file.name) ? 'selected' : ''}" 
         data-filename="${escapeHtml(file.name)}" 
         style="animation-delay: ${Math.min(index * 0.05, 0.25)}s">
      ${isSelectMode ? `
        <div class="file-checkbox">
          <input type="checkbox" id="check-${index}" ${selectedFiles.has(file.name) ? 'checked' : ''}>
          <label for="check-${index}"></label>
        </div>
      ` : ''}
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
        <button class="delete-btn" data-filename="${escapeHtml(file.name)}" title="Delete">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
          </svg>
        </button>
      </div>
    </div>
  `).join("")

  // Add event listeners with delegation
  elements.fileList.querySelectorAll(".download-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      downloadFile(btn.dataset.filename)
    })
  })

  elements.fileList.querySelectorAll(".delete-btn").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation()
      await handleDeleteFile(btn.dataset.filename)
    })
  })

  // File card click for selection mode
  if (isSelectMode) {
    elements.fileList.querySelectorAll(".file-card").forEach(card => {
      card.addEventListener("click", () => {
        const filename = card.dataset.filename
        if (selectedFiles.has(filename)) {
          selectedFiles.delete(filename)
          card.classList.remove("selected")
        } else {
          selectedFiles.add(filename)
          card.classList.add("selected")
        }
        updateBatchActionsUI()
      })
    })
  }
}

const downloadFile = (filename) => {
  const link = document.createElement("a")
  link.href = API.download(filename, false)
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  showToast(`Downloading ${filename}`, "success")
}

const handleDeleteFile = async (filename) => {
  if (!confirm(`Delete "${filename}"?`)) return

  try {
    await deleteFile(filename)
    showToast(`Deleted ${filename}`, "success")
    await handleRefresh()
  } catch (error) {
    showToast(`Failed to delete ${filename}`, "error")
  }
}

const showLoading = () => {
  getElements().fileList.innerHTML = `
    <div class="loading">
      <div class="spinner"></div>
      <span>Loading files...</span>
    </div>
  `
}

const showToast = (message, type = "info") => {
  const icons = { success: "✓", error: "✕", warning: "⚠", info: "ℹ" }
  const elements = getElements()

  const toast = document.createElement("div")
  toast.className = `toast ${type}`
  toast.innerHTML = `
    <span class="toast-icon">${icons[type]}</span>
    <span class="toast-message">${escapeHtml(message)}</span>
  `

  elements.toastContainer.appendChild(toast)

  setTimeout(() => {
    toast.style.opacity = "0"
    toast.style.transform = "translateY(10px)"
    setTimeout(() => toast.remove(), 300)
  }, 3000)
}

// ==================== Modal Functions ====================
const openUploadModal = () => {
  const elements = getElements()
  elements.uploadModal.classList.add("active")
  elements.uploadProgressContainer.hidden = true
  elements.uploadArea.style.display = uploadQueue.length > 0 ? "none" : "flex"
  elements.fileQueue.hidden = uploadQueue.length === 0
  elements.startUploadBtn.disabled = uploadQueue.length === 0
  elements.startUploadBtn.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
      <polyline points="17 8 12 3 7 8"/>
      <line x1="12" y1="3" x2="12" y2="15"/>
    </svg>
    Upload All
  `
  elements.cancelUploadBtn.textContent = "Cancel"
}

const closeUploadModal = () => {
  const elements = getElements()

  if (isUploading) {
    if (!confirm("Cancel all uploads?")) return
    cancelAllUploads()
  }

  elements.uploadModal.classList.remove("active")
  clearQueue()
}

// ==================== Select Mode ====================
const toggleSelectMode = () => {
  const elements = getElements()
  isSelectMode = !isSelectMode
  selectedFiles.clear()

  elements.selectModeBtn.classList.toggle("active", isSelectMode)
  elements.batchActions.hidden = !isSelectMode

  renderFiles()
  updateBatchActionsUI()
}

const updateBatchActionsUI = () => {
  const elements = getElements()
  const count = selectedFiles.size
  elements.downloadSelectedBtn.disabled = count === 0
  elements.deleteSelectedBtn.disabled = count === 0
  elements.selectAllBtn.textContent = count === files.length ? "Deselect All" : "Select All"
}

const selectAll = () => {
  if (selectedFiles.size === files.length) {
    selectedFiles.clear()
  } else {
    files.forEach(f => selectedFiles.add(f.name))
  }
  renderFiles()
  updateBatchActionsUI()
}

const downloadSelected = async () => {
  for (const filename of selectedFiles) {
    downloadFile(filename)
    await new Promise(r => setTimeout(r, 300)) // Stagger downloads
  }
}

const deleteSelected = async () => {
  if (!confirm(`Delete ${selectedFiles.size} selected files?`)) return

  const deletePromises = Array.from(selectedFiles).map(filename =>
    deleteFile(filename).catch(e => ({ error: e, filename }))
  )

  const results = await Promise.all(deletePromises)
  const failed = results.filter(r => r?.error).length

  if (failed > 0) {
    showToast(`Deleted ${selectedFiles.size - failed} files. ${failed} failed.`, "warning")
  } else {
    showToast(`Deleted ${selectedFiles.size} files`, "success")
  }

  selectedFiles.clear()
  isSelectMode = false
  getElements().selectModeBtn.classList.remove("active")
  getElements().batchActions.hidden = true
  await handleRefresh()
}

// ==================== Theme Toggle ====================
const toggleTheme = () => {
  isDarkTheme = !isDarkTheme
  document.body.classList.toggle("theme-light", !isDarkTheme)
  localStorage.setItem("flashare-theme", isDarkTheme ? "dark" : "light")

  // Update theme color meta tag
  const themeColor = isDarkTheme ? "#0a0a0f" : "#f5f5f7"
  document.querySelector('meta[name="theme-color"]').content = themeColor
}

const loadTheme = () => {
  const saved = localStorage.getItem("flashare-theme")
  if (saved === "light") {
    isDarkTheme = false
    document.body.classList.add("theme-light")
  }
}

// ==================== Event Handlers ====================
const handleRefresh = debounce(async () => {
  showLoading()
  try {
    files = await fetchFiles()
    renderFiles()
    showToast("Files refreshed", "success")
  } catch (error) {
    showToast("Failed to load files", "error")
    getElements().fileList.innerHTML = `
      <div class="empty-state">
        <p>Failed to load files</p>
        <p>Check your connection and try again</p>
      </div>
    `
  }
}, 300)

const handleFileSelect = async (fileList) => {
  if (fileList.length === 0) return
  await addToQueue(fileList)
}

// ==================== Initialization ====================
const init = async () => {
  loadTheme()

  const elements = getElements()

  // Check for mobile
  const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)
  if (elements.mobileCapture) {
    elements.mobileCapture.style.display = isMobile ? "grid" : "none"
  }

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
  elements.closeModalBtn?.addEventListener("click", closeUploadModal)
  elements.clearQueueBtn.addEventListener("click", clearQueue)
  elements.startUploadBtn.addEventListener("click", uploadAllFiles)
  elements.selectModeBtn.addEventListener("click", toggleSelectMode)
  elements.selectAllBtn.addEventListener("click", selectAll)
  elements.downloadSelectedBtn.addEventListener("click", downloadSelected)
  elements.deleteSelectedBtn.addEventListener("click", deleteSelected)
  elements.themeToggle.addEventListener("click", toggleTheme)

  // Modal backdrop click
  elements.uploadModal.querySelector(".modal-backdrop").addEventListener("click", closeUploadModal)

  // Upload area click
  elements.uploadArea.addEventListener("click", () => elements.hiddenFileInput.click())

  // File input change (multi-file)
  elements.hiddenFileInput.addEventListener("change", (e) => {
    if (e.target.files?.length > 0) {
      handleFileSelect(e.target.files)
      e.target.value = "" // Reset for re-selection
    }
  })

  // Mobile capture buttons
  if (elements.capturePhotoBtn) {
    elements.capturePhotoBtn.addEventListener("click", () => elements.cameraInput.click())
    elements.cameraInput.addEventListener("change", (e) => {
      if (e.target.files?.length > 0) {
        handleFileSelect(e.target.files)
        openUploadModal()
      }
    })
  }

  if (elements.captureGalleryBtn) {
    elements.captureGalleryBtn.addEventListener("click", () => elements.galleryInput.click())
    elements.galleryInput.addEventListener("change", (e) => {
      if (e.target.files?.length > 0) {
        handleFileSelect(e.target.files)
        openUploadModal()
      }
    })
  }

  // Drag and drop (multi-file)
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
    if (e.dataTransfer?.files?.length > 0) {
      handleFileSelect(e.dataTransfer.files)
    }
  })

  // Global drag and drop on window
  const preventDefaults = (e) => { e.preventDefault(); e.stopPropagation() }
    ;["dragenter", "dragover", "dragleave", "drop"].forEach(event => {
      document.body.addEventListener(event, preventDefaults, false)
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

  // Keyboard shortcuts
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (getElements().uploadModal.classList.contains("active")) {
        closeUploadModal()
      }
    }
  })
}

// Start the app
document.addEventListener("DOMContentLoaded", init)
