// Package server provides the HTTP server for Flashare.
package server

import (
	"embed"
	"fmt"
	"io"
	"io/fs"
	"mime"
	"mime/multipart"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/fiber/v2/middleware/filesystem"
	"github.com/gofiber/fiber/v2/middleware/recover"
	"github.com/klauspost/compress/zstd"

	"github.com/Abhijit-without-h/flashare/internal/qr"
)

//go:embed static/*
var staticFS embed.FS

// Config holds server configuration.
type Config struct {
	Host       string
	Port       int
	UploadsDir string
}

// Server represents the Flashare HTTP server.
type Server struct {
	config Config
	app    *fiber.App
}

// FileInfo represents information about a file.
type FileInfo struct {
	Name      string  `json:"name"`
	Size      int64   `json:"size"`
	SizeHuman string  `json:"size_human"`
	Modified  float64 `json:"modified"`
	Type      string  `json:"type"`
}

// UploadResult represents the result of an upload.
type UploadResult struct {
	Success   bool   `json:"success"`
	Filename  string `json:"filename"`
	Size      int64  `json:"size,omitempty"`
	SizeHuman string `json:"size_human,omitempty"`
	Type      string `json:"type,omitempty"`
	Error     string `json:"error,omitempty"`
}

// New creates a new server instance.
func New(config Config) *Server {
	app := fiber.New(fiber.Config{
		AppName:               "Flashare",
		DisableStartupMessage: true,
		BodyLimit:             10 * 1024 * 1024 * 1024, // 10GB limit
		StreamRequestBody:     true,
	})

	s := &Server{
		config: config,
		app:    app,
	}

	s.setupMiddleware()
	s.setupRoutes()

	return s
}

// setupMiddleware configures middleware.
func (s *Server) setupMiddleware() {
	// Panic recovery
	s.app.Use(recover.New())

	// CORS for browser access
	s.app.Use(cors.New(cors.Config{
		AllowOrigins: "*",
		AllowMethods: "GET,POST,DELETE,OPTIONS",
		AllowHeaders: "*",
	}))
}

// setupRoutes configures API routes.
func (s *Server) setupRoutes() {
	// API routes
	api := s.app.Group("/api")
	api.Get("/files", s.handleListFiles)
	api.Get("/download/:filename", s.handleDownload)
	api.Post("/upload", s.handleUpload)
	api.Post("/upload-multiple", s.handleUploadMultiple)
	api.Delete("/files/:filename", s.handleDelete)
	api.Delete("/files", s.handleDeleteMultiple)
	api.Get("/qr", s.handleQR)
	api.Get("/qr.png", s.handleQRImage)
	api.Get("/status", s.handleStatus)

	// Serve static files from embedded FS
	staticSub, _ := fs.Sub(staticFS, "static")
	s.app.Use("/static", filesystem.New(filesystem.Config{
		Root:       http.FS(staticSub),
		PathPrefix: "",
	}))

	// Root serves the index page
	s.app.Get("/", func(c *fiber.Ctx) error {
		data, err := staticFS.ReadFile("static/index.html")
		if err != nil {
			return c.Status(500).SendString("UI not found")
		}
		c.Set("Content-Type", "text/html; charset=utf-8")
		return c.Send(data)
	})
}

// Start starts the server.
func (s *Server) Start() error {
	addr := fmt.Sprintf("%s:%d", s.config.Host, s.config.Port)
	return s.app.Listen(addr)
}

// handleListFiles returns a list of available files.
func (s *Server) handleListFiles(c *fiber.Ctx) error {
	files := []FileInfo{}

	entries, err := os.ReadDir(s.config.UploadsDir)
	if err != nil {
		return c.JSON(files)
	}

	// Process files in parallel using goroutines
	var wg sync.WaitGroup
	var mu sync.Mutex

	for _, entry := range entries {
		if entry.IsDir() || strings.HasPrefix(entry.Name(), ".") {
			continue
		}

		wg.Add(1)
		go func(entry os.DirEntry) {
			defer wg.Done()

			info, err := entry.Info()
			if err != nil {
				return
			}

			fileInfo := FileInfo{
				Name:      info.Name(),
				Size:      info.Size(),
				SizeHuman: formatSize(info.Size()),
				Modified:  float64(info.ModTime().Unix()),
				Type:      getFileType(info.Name()),
			}

			mu.Lock()
			files = append(files, fileInfo)
			mu.Unlock()
		}(entry)
	}

	wg.Wait()

	// Sort by modification time (newest first)
	sort.Slice(files, func(i, j int) bool {
		return files[i].Modified > files[j].Modified
	})

	return c.JSON(files)
}

// handleDownload streams a file with optional compression.
func (s *Server) handleDownload(c *fiber.Ctx) error {
	filename := c.Params("filename")
	compressed := c.QueryBool("compressed", true)

	filePath := filepath.Join(s.config.UploadsDir, filepath.Clean(filename))

	// Security check
	if !strings.HasPrefix(filePath, s.config.UploadsDir) {
		return c.Status(403).JSON(fiber.Map{"error": "Access denied"})
	}

	file, err := os.Open(filePath)
	if err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "File not found"})
	}
	defer file.Close()

	stat, _ := file.Stat()

	// Set headers
	c.Set("Content-Disposition", fmt.Sprintf(`attachment; filename="%s"`, filename))

	if compressed {
		c.Set("Content-Encoding", "zstd")
		c.Set("Content-Type", "application/octet-stream")

		// Stream with zstd compression
		encoder, err := zstd.NewWriter(c.Response().BodyWriter(), zstd.WithEncoderLevel(zstd.SpeedFastest))
		if err != nil {
			return c.Status(500).JSON(fiber.Map{"error": "Compression error"})
		}
		defer encoder.Close()

		_, err = io.Copy(encoder, file)
		return err
	}

	c.Set("Content-Length", fmt.Sprintf("%d", stat.Size()))
	c.Set("Content-Type", mime.TypeByExtension(filepath.Ext(filename)))

	return c.SendStream(file)
}

// handleUpload handles single file upload.
func (s *Server) handleUpload(c *fiber.Ctx) error {
	file, err := c.FormFile("file")
	if err != nil {
		return c.Status(400).JSON(UploadResult{Success: false, Error: "No file provided"})
	}

	result := s.saveUploadedFile(file)
	if !result.Success {
		return c.Status(400).JSON(result)
	}

	return c.JSON(result)
}

// handleUploadMultiple handles multiple file uploads in parallel.
func (s *Server) handleUploadMultiple(c *fiber.Ctx) error {
	form, err := c.MultipartForm()
	if err != nil {
		return c.Status(400).JSON(fiber.Map{"success": false, "error": "Invalid form data"})
	}

	files := form.File["files"]
	if len(files) == 0 {
		return c.Status(400).JSON(fiber.Map{"success": false, "error": "No files provided"})
	}

	// Process uploads in parallel
	results := make([]UploadResult, len(files))
	var wg sync.WaitGroup

	for i, file := range files {
		wg.Add(1)
		go func(idx int, f *multipart.FileHeader) {
			defer wg.Done()
			results[idx] = s.saveUploadedFile(f)
		}(i, file)
	}

	wg.Wait()

	// Calculate summary
	var successful, failed int
	var totalSize int64
	for _, r := range results {
		if r.Success {
			successful++
			totalSize += r.Size
		} else {
			failed++
		}
	}

	return c.JSON(fiber.Map{
		"success": failed == 0,
		"files":   results,
		"summary": fiber.Map{
			"total":            len(files),
			"successful":       successful,
			"failed":           failed,
			"total_size":       totalSize,
			"total_size_human": formatSize(totalSize),
		},
	})
}

// saveUploadedFile saves an uploaded file to disk.
func (s *Server) saveUploadedFile(file *multipart.FileHeader) UploadResult {
	filename := filepath.Base(file.Filename)
	destPath := filepath.Join(s.config.UploadsDir, filename)

	// Handle duplicates
	if _, err := os.Stat(destPath); err == nil {
		ext := filepath.Ext(destPath)
		base := destPath[:len(destPath)-len(ext)]
		for i := 1; ; i++ {
			destPath = fmt.Sprintf("%s_%d%s", base, i, ext)
			if _, err := os.Stat(destPath); os.IsNotExist(err) {
				break
			}
		}
		filename = filepath.Base(destPath)
	}

	// Open source
	src, err := file.Open()
	if err != nil {
		return UploadResult{Success: false, Filename: filename, Error: "Failed to read file"}
	}
	defer src.Close()

	// Create destination
	dst, err := os.Create(destPath)
	if err != nil {
		return UploadResult{Success: false, Filename: filename, Error: "Failed to create file"}
	}
	defer dst.Close()

	// Copy with buffered I/O for performance
	written, err := io.Copy(dst, src)
	if err != nil {
		os.Remove(destPath)
		return UploadResult{Success: false, Filename: filename, Error: "Failed to save file"}
	}

	return UploadResult{
		Success:   true,
		Filename:  filename,
		Size:      written,
		SizeHuman: formatSize(written),
		Type:      getFileType(filename),
	}
}

// handleDelete deletes a single file.
func (s *Server) handleDelete(c *fiber.Ctx) error {
	filename := c.Params("filename")
	filePath := filepath.Join(s.config.UploadsDir, filepath.Clean(filename))

	// Security check
	if !strings.HasPrefix(filePath, s.config.UploadsDir) {
		return c.Status(403).JSON(fiber.Map{"error": "Access denied"})
	}

	if err := os.Remove(filePath); err != nil {
		return c.Status(404).JSON(fiber.Map{"error": "File not found"})
	}

	return c.JSON(fiber.Map{"success": true, "deleted": filename})
}

// handleDeleteMultiple deletes multiple files in parallel.
func (s *Server) handleDeleteMultiple(c *fiber.Ctx) error {
	var body struct {
		Filenames []string `json:"filenames"`
	}

	if err := c.BodyParser(&body); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid request"})
	}

	type deleteResult struct {
		Filename string `json:"filename"`
		Success  bool   `json:"success"`
		Error    string `json:"error,omitempty"`
	}

	results := make([]deleteResult, len(body.Filenames))
	var wg sync.WaitGroup

	for i, filename := range body.Filenames {
		wg.Add(1)
		go func(idx int, fname string) {
			defer wg.Done()

			filePath := filepath.Join(s.config.UploadsDir, filepath.Clean(fname))

			if !strings.HasPrefix(filePath, s.config.UploadsDir) {
				results[idx] = deleteResult{Filename: fname, Success: false, Error: "Access denied"}
				return
			}

			if err := os.Remove(filePath); err != nil {
				results[idx] = deleteResult{Filename: fname, Success: false, Error: "File not found"}
				return
			}

			results[idx] = deleteResult{Filename: fname, Success: true}
		}(i, filename)
	}

	wg.Wait()

	var successful int
	for _, r := range results {
		if r.Success {
			successful++
		}
	}

	return c.JSON(fiber.Map{
		"success": successful == len(body.Filenames),
		"results": results,
		"summary": fiber.Map{
			"total":      len(body.Filenames),
			"successful": successful,
			"failed":     len(body.Filenames) - successful,
		},
	})
}

// handleQR returns QR code data.
func (s *Server) handleQR(c *fiber.Ctx) error {
	url := fmt.Sprintf("http://%s:%d", getOutboundIP(), s.config.Port)
	return c.JSON(fiber.Map{
		"url":     url,
		"port":    s.config.Port,
		"version": "1.0.0",
	})
}

// handleQRImage returns QR code as PNG.
func (s *Server) handleQRImage(c *fiber.Ctx) error {
	url := fmt.Sprintf("http://%s:%d", getOutboundIP(), s.config.Port)
	png, err := qr.GeneratePNG(url, 256)
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "Failed to generate QR"})
	}
	c.Set("Content-Type", "image/png")
	return c.Send(png)
}

// handleStatus returns server status.
func (s *Server) handleStatus(c *fiber.Ctx) error {
	entries, _ := os.ReadDir(s.config.UploadsDir)

	var fileCount int
	var totalSize int64

	for _, entry := range entries {
		if !entry.IsDir() && !strings.HasPrefix(entry.Name(), ".") {
			fileCount++
			if info, err := entry.Info(); err == nil {
				totalSize += info.Size()
			}
		}
	}

	return c.JSON(fiber.Map{
		"status":           "online",
		"url":              fmt.Sprintf("http://%s:%d", getOutboundIP(), s.config.Port),
		"uploads_dir":      s.config.UploadsDir,
		"file_count":       fileCount,
		"total_size":       totalSize,
		"total_size_human": formatSize(totalSize),
		"uptime":           time.Since(startTime).String(),
	})
}

var startTime = time.Now()

// Utility functions

func formatSize(bytes int64) string {
	const unit = 1024
	if bytes < unit {
		return fmt.Sprintf("%d B", bytes)
	}
	div, exp := int64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %cB", float64(bytes)/float64(div), "KMGTPE"[exp])
}

func getFileType(filename string) string {
	ext := strings.ToLower(filepath.Ext(filename))
	switch ext {
	case ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".heic", ".bmp":
		return "image"
	case ".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v":
		return "video"
	case ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a":
		return "audio"
	case ".pdf", ".doc", ".docx", ".txt", ".rtf", ".md", ".xls", ".xlsx", ".csv":
		return "document"
	default:
		return "file"
	}
}

func getOutboundIP() string {
	addrs, err := net.InterfaceAddrs()
	if err != nil {
		return "127.0.0.1"
	}

	for _, addr := range addrs {
		if ipnet, ok := addr.(*net.IPNet); ok && !ipnet.IP.IsLoopback() {
			if ipnet.IP.To4() != nil {
				return ipnet.IP.String()
			}
		}
	}
	return "127.0.0.1"
}
