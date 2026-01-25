// Package cli provides the command-line interface for Flashare.
package cli

import (
	"fmt"
	"net"
	"os"
	"path/filepath"

	"github.com/charmbracelet/lipgloss"
	"github.com/spf13/cobra"

	"github.com/Abhijit-without-h/flashare/internal/qr"
	"github.com/Abhijit-without-h/flashare/internal/server"
	"github.com/Abhijit-without-h/flashare/internal/tui"
)

var (
	// Version info set by main
	versionInfo struct {
		Version string
		Commit  string
		Date    string
	}

	// Global flags
	port    int
	host    string
	dataDir string
	noTUI   bool
)

// Styles using lipgloss
var (
	titleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("#818cf8"))

	accentStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#6366f1"))

	successStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#10b981"))

	warningStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#f59e0b"))

	errorStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#ef4444"))

	infoStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#3b82f6"))

	dimStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#6b7280"))
)

// SetVersionInfo sets version information from main package.
func SetVersionInfo(version, commit, date string) {
	versionInfo.Version = version
	versionInfo.Commit = commit
	versionInfo.Date = date
}

// rootCmd is the base command.
var rootCmd = &cobra.Command{
	Use:   "flashare",
	Short: "⚡ Flashare - CLI-First Hybrid File Sharing Tool",
	Long: `⚡ Flashare - CLI-First Hybrid File Sharing Tool

A high-performance file sharing tool with a modern mobile web UI.
Share files between your laptop and phone instantly.

Features:
  • Beautiful animated TUI interface
  • Fuzzy file selection with built-in picker
  • Zstandard compression for fast transfers  
  • QR code for instant mobile connection
  • Modern glassmorphism web UI
  • Multi-file parallel uploads`,
	Run: func(cmd *cobra.Command, args []string) {
		// Ensure data directory exists
		uploadsDir := filepath.Join(dataDir, "uploads")
		if err := os.MkdirAll(uploadsDir, 0755); err != nil {
			printError("Failed to create uploads directory: %v", err)
			os.Exit(1)
		}

		// Start TUI by default, or fallback to CLI mode
		if !noTUI {
			if err := tui.Run(uploadsDir, func(dir string) {
				startServerInBackground(dir)
			}); err != nil {
				printError("TUI error: %v", err)
				os.Exit(1)
			}
		} else {
			printBanner()
			startServer(uploadsDir)
		}
	},
}

// sendCmd starts the server to send files.
var sendCmd = &cobra.Command{
	Use:   "send [files...]",
	Short: "Share files (starts server with QR code)",
	Long:  "Start the Flashare server to share files. Opens web UI for mobile access.",
	Run: func(cmd *cobra.Command, args []string) {
		printBanner()

		// Ensure data directory exists
		uploadsDir := filepath.Join(dataDir, "uploads")
		if err := os.MkdirAll(uploadsDir, 0755); err != nil {
			printError("Failed to create uploads directory: %v", err)
			os.Exit(1)
		}

		// Copy specified files to uploads directory
		if len(args) > 0 {
			for _, file := range args {
				if err := copyFileToUploads(file, uploadsDir); err != nil {
					printWarning("Failed to copy %s: %v", file, err)
				} else {
					printSuccess("Added: %s", filepath.Base(file))
				}
			}
		}

		// Start server
		startServer(uploadsDir)
	},
}

// receiveCmd starts the server in receive mode.
var receiveCmd = &cobra.Command{
	Use:   "receive",
	Short: "Receive files (starts server for uploads)",
	Long:  "Start the Flashare server to receive files from mobile devices.",
	Run: func(cmd *cobra.Command, args []string) {
		printBanner()

		uploadsDir := filepath.Join(dataDir, "uploads")
		if err := os.MkdirAll(uploadsDir, 0755); err != nil {
			printError("Failed to create uploads directory: %v", err)
			os.Exit(1)
		}

		printInfo("Ready to receive files...")
		startServer(uploadsDir)
	},
}

// versionCmd shows version information.
var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Show version information",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Printf("Flashare %s\n", versionInfo.Version)
		fmt.Printf("  Commit: %s\n", versionInfo.Commit)
		fmt.Printf("  Built:  %s\n", versionInfo.Date)
	},
}

func init() {
	// Get default data directory
	homeDir, _ := os.UserHomeDir()
	defaultDataDir := filepath.Join(homeDir, ".flashare")

	// Global flags
	rootCmd.PersistentFlags().IntVarP(&port, "port", "p", 8000, "Server port")
	rootCmd.PersistentFlags().StringVarP(&host, "host", "H", "0.0.0.0", "Server host")
	rootCmd.PersistentFlags().StringVarP(&dataDir, "data-dir", "d", defaultDataDir, "Data directory for uploads")
	rootCmd.PersistentFlags().BoolVar(&noTUI, "no-tui", false, "Disable TUI, use simple CLI mode")

	// Add subcommands
	rootCmd.AddCommand(sendCmd)
	rootCmd.AddCommand(receiveCmd)
	rootCmd.AddCommand(versionCmd)
}

// Execute runs the CLI.
func Execute() error {
	return rootCmd.Execute()
}

// startServer initializes and starts the HTTP server.
func startServer(uploadsDir string) {
	// Get server URL
	ip := getOutboundIP()
	serverURL := fmt.Sprintf("http://%s:%d", ip, port)

	// Print server info
	fmt.Println()
	printInfo("Server starting on %s", accentStyle.Render(serverURL))
	fmt.Println()

	// Print QR code
	qr.PrintQRCode(serverURL)
	fmt.Println()

	printInfo("Scan QR code or open URL on your phone")
	printDim("Press Ctrl+C to stop")
	fmt.Println()

	// Create and start server
	srv := server.New(server.Config{
		Host:       host,
		Port:       port,
		UploadsDir: uploadsDir,
	})

	if err := srv.Start(); err != nil {
		printError("Server error: %v", err)
		os.Exit(1)
	}
}

// startServerInBackground starts server without blocking.
func startServerInBackground(uploadsDir string) {
	srv := server.New(server.Config{
		Host:       host,
		Port:       port,
		UploadsDir: uploadsDir,
	})

	go func() {
		if err := srv.Start(); err != nil {
			fmt.Fprintf(os.Stderr, "Server error: %v\n", err)
		}
	}()
}

// copyFileToUploads copies a file to the uploads directory.
func copyFileToUploads(src, uploadsDir string) error {
	srcInfo, err := os.Stat(src)
	if err != nil {
		return err
	}

	if srcInfo.IsDir() {
		return fmt.Errorf("directories not supported yet")
	}

	data, err := os.ReadFile(src)
	if err != nil {
		return err
	}

	dst := filepath.Join(uploadsDir, filepath.Base(src))

	// Handle duplicates
	if _, err := os.Stat(dst); err == nil {
		ext := filepath.Ext(dst)
		base := dst[:len(dst)-len(ext)]
		for i := 1; ; i++ {
			dst = fmt.Sprintf("%s_%d%s", base, i, ext)
			if _, err := os.Stat(dst); os.IsNotExist(err) {
				break
			}
		}
	}

	return os.WriteFile(dst, data, 0644)
}

// getOutboundIP gets the preferred outbound IP address.
func getOutboundIP() string {
	conn, err := net.Dial("udp", "8.8.8.8:80")
	if err != nil {
		return "127.0.0.1"
	}
	defer conn.Close()

	localAddr := conn.LocalAddr().(*net.UDPAddr)
	return localAddr.IP.String()
}

// Print helpers
func printBanner() {
	banner := `
  ⚡ Flashare
  ` + dimStyle.Render("Fast file sharing between devices")
	fmt.Println(titleStyle.Render(banner))
	fmt.Println()
}

func printSuccess(format string, args ...interface{}) {
	msg := fmt.Sprintf(format, args...)
	fmt.Println(successStyle.Render("✓ " + msg))
}

func printWarning(format string, args ...interface{}) {
	msg := fmt.Sprintf(format, args...)
	fmt.Println(warningStyle.Render("⚠ " + msg))
}

func printError(format string, args ...interface{}) {
	msg := fmt.Sprintf(format, args...)
	fmt.Println(errorStyle.Render("✕ " + msg))
}

func printInfo(format string, args ...interface{}) {
	msg := fmt.Sprintf(format, args...)
	fmt.Println(infoStyle.Render("→ " + msg))
}

func printDim(format string, args ...interface{}) {
	msg := fmt.Sprintf(format, args...)
	fmt.Println(dimStyle.Render("  " + msg))
}
