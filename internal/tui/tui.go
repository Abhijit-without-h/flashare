// Package tui provides a beautiful animated terminal UI for Flashare.
package tui

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/filepicker"
	"github.com/charmbracelet/bubbles/progress"
	"github.com/charmbracelet/bubbles/spinner"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Styles
var (
	titleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("#818cf8")).
			MarginBottom(1)

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

	selectedStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#a855f7")).
			Bold(true)

	boxStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.Color("#6366f1")).
			Padding(1, 2).
			MarginTop(1)

	helpStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#6b7280")).
			MarginTop(1)
)

// State represents the current TUI state.
type State int

const (
	StateMenu State = iota
	StateFilePicker
	StateFileList
	StateUploading
	StateServer
)

// Model represents the TUI model.
type Model struct {
	state         State
	width         int
	height        int
	spinner       spinner.Model
	progress      progress.Model
	filePicker    filepicker.Model
	selectedFiles []string
	quitting      bool
	serverURL     string
	uploadsDir    string
	startServer   func(string)

	// File list
	files  []FileInfo
	cursor int

	// Upload progress
	uploadIndex int
	uploadTotal int
	uploadFile  string
}

// FileInfo represents file information.
type FileInfo struct {
	Name string
	Size int64
	Path string
}

// Messages
type tickMsg time.Time
type serverStartedMsg struct{ url string }
type filesLoadedMsg []FileInfo
type uploadProgressMsg float64
type uploadCompleteMsg struct{}

// NewModel creates a new TUI model.
func NewModel(uploadsDir string, startServer func(string)) Model {
	// Initialize spinner with dots
	s := spinner.New()
	s.Spinner = spinner.Dot
	s.Style = lipgloss.NewStyle().Foreground(lipgloss.Color("#6366f1"))

	// Initialize progress bar
	p := progress.New(
		progress.WithDefaultGradient(),
		progress.WithWidth(40),
	)

	// Initialize file picker
	fp := filepicker.New()
	fp.AllowedTypes = []string{".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mov", ".pdf", ".doc", ".docx", ".txt", ".zip"}
	fp.CurrentDirectory, _ = os.UserHomeDir()
	fp.ShowHidden = false
	fp.Height = 10

	return Model{
		state:       StateMenu,
		spinner:     s,
		progress:    p,
		filePicker:  fp,
		uploadsDir:  uploadsDir,
		startServer: startServer,
	}
}

// Init initializes the model.
func (m Model) Init() tea.Cmd {
	return tea.Batch(
		m.spinner.Tick,
		tea.EnterAltScreen,
	)
}

// Update handles messages.
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		m.progress.Width = msg.Width - 20
		m.filePicker.Height = msg.Height - 10
		return m, nil

	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			m.quitting = true
			return m, tea.Quit
		case "esc":
			if m.state != StateMenu && m.state != StateServer {
				m.state = StateMenu
				return m, nil
			}
		}

	case spinner.TickMsg:
		var cmd tea.Cmd
		m.spinner, cmd = m.spinner.Update(msg)
		return m, cmd

	case progress.FrameMsg:
		progressModel, cmd := m.progress.Update(msg)
		m.progress = progressModel.(progress.Model)
		return m, cmd
	}

	// State-specific updates
	switch m.state {
	case StateMenu:
		return m.updateMenu(msg)
	case StateFilePicker:
		return m.updateFilePicker(msg)
	case StateFileList:
		return m.updateFileList(msg)
	case StateServer:
		return m.updateServer(msg)
	}

	return m, nil
}

func (m Model) updateMenu(msg tea.Msg) (tea.Model, tea.Cmd) {
	if keyMsg, ok := msg.(tea.KeyMsg); ok {
		switch keyMsg.String() {
		case "1", "s":
			m.state = StateFilePicker
			return m, m.filePicker.Init()
		case "2", "r":
			m.state = StateServer
			return m, m.startServerCmd()
		case "3", "q":
			m.quitting = true
			return m, tea.Quit
		}
	}
	return m, nil
}

func (m Model) updateFilePicker(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd
	m.filePicker, cmd = m.filePicker.Update(msg)

	if didSelect, path := m.filePicker.DidSelectFile(msg); didSelect {
		m.selectedFiles = append(m.selectedFiles, path)
	}

	if keyMsg, ok := msg.(tea.KeyMsg); ok {
		switch keyMsg.String() {
		case "enter":
			if len(m.selectedFiles) > 0 {
				m.state = StateServer
				return m, tea.Batch(m.copyFilesCmd(), m.startServerCmd())
			}
		case "tab":
			// Toggle selection
			if path := m.filePicker.Path; path != "" {
				// Toggle file selection
				found := false
				for i, f := range m.selectedFiles {
					if f == path {
						m.selectedFiles = append(m.selectedFiles[:i], m.selectedFiles[i+1:]...)
						found = true
						break
					}
				}
				if !found {
					m.selectedFiles = append(m.selectedFiles, path)
				}
			}
		}
	}

	return m, cmd
}

func (m Model) updateFileList(msg tea.Msg) (tea.Model, tea.Cmd) {
	if keyMsg, ok := msg.(tea.KeyMsg); ok {
		switch keyMsg.String() {
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			if m.cursor < len(m.files)-1 {
				m.cursor++
			}
		case "enter":
			if m.cursor < len(m.files) {
				// Download selected file
			}
		}
	}
	return m, nil
}

func (m Model) updateServer(msg tea.Msg) (tea.Model, tea.Cmd) {
	if _, ok := msg.(serverStartedMsg); ok {
		return m, nil
	}
	return m, nil
}

// View renders the TUI.
func (m Model) View() string {
	if m.quitting {
		return successStyle.Render("Thanks for using Flashare! ⚡\n")
	}

	var content string

	switch m.state {
	case StateMenu:
		content = m.viewMenu()
	case StateFilePicker:
		content = m.viewFilePicker()
	case StateFileList:
		content = m.viewFileList()
	case StateServer:
		content = m.viewServer()
	default:
		content = m.viewMenu()
	}

	return content
}

func (m Model) viewMenu() string {
	title := titleStyle.Render(`
  ⚡ Flashare
  ` + dimStyle.Render("Fast file sharing between devices"))

	menu := boxStyle.Render(fmt.Sprintf(`%s Select an option:

  %s  Send files
  %s  Receive files  
  %s  Quit

%s`,
		accentStyle.Render("→"),
		selectedStyle.Render("[1]"),
		selectedStyle.Render("[2]"),
		selectedStyle.Render("[3]"),
		dimStyle.Render("Press number or first letter to select"),
	))

	help := helpStyle.Render("Press 'q' to quit")

	return fmt.Sprintf("%s\n%s\n%s", title, menu, help)
}

func (m Model) viewFilePicker() string {
	title := titleStyle.Render("📁 Select files to share")

	selected := ""
	if len(m.selectedFiles) > 0 {
		files := make([]string, len(m.selectedFiles))
		for i, f := range m.selectedFiles {
			files[i] = successStyle.Render("✓ " + filepath.Base(f))
		}
		selected = boxStyle.Render(fmt.Sprintf("Selected (%d):\n%s", len(m.selectedFiles), strings.Join(files, "\n")))
	}

	picker := m.filePicker.View()

	help := helpStyle.Render("Tab: select/deselect • Enter: confirm • Esc: back")

	return fmt.Sprintf("%s\n\n%s\n%s\n%s", title, picker, selected, help)
}

func (m Model) viewFileList() string {
	title := titleStyle.Render("📋 Available Files")

	if len(m.files) == 0 {
		return fmt.Sprintf("%s\n\n%s",
			title,
			dimStyle.Render("No files available"),
		)
	}

	var items []string
	for i, f := range m.files {
		cursor := "  "
		style := dimStyle
		if i == m.cursor {
			cursor = accentStyle.Render("→ ")
			style = accentStyle
		}
		items = append(items, fmt.Sprintf("%s%s %s",
			cursor,
			style.Render(f.Name),
			dimStyle.Render(formatSize(f.Size)),
		))
	}

	return fmt.Sprintf("%s\n\n%s", title, strings.Join(items, "\n"))
}

func (m Model) viewServer() string {
	title := titleStyle.Render("⚡ Flashare Server")

	status := boxStyle.Render(fmt.Sprintf(`%s Server is running!

  %s %s

  %s Scan QR code or open URL on your phone

%s`,
		m.spinner.View(),
		infoStyle.Render("URL:"),
		accentStyle.Render(m.serverURL),
		successStyle.Render("→"),
		dimStyle.Render("Press Ctrl+C to stop"),
	))

	return fmt.Sprintf("%s\n%s", title, status)
}

// Commands
func (m Model) startServerCmd() tea.Cmd {
	return func() tea.Msg {
		go m.startServer(m.uploadsDir)
		return serverStartedMsg{url: m.serverURL}
	}
}

func (m Model) copyFilesCmd() tea.Cmd {
	return func() tea.Msg {
		for _, src := range m.selectedFiles {
			dst := filepath.Join(m.uploadsDir, filepath.Base(src))
			data, err := os.ReadFile(src)
			if err != nil {
				continue
			}
			os.WriteFile(dst, data, 0644)
		}
		return nil
	}
}

// Utility
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

// Run starts the TUI.
func Run(uploadsDir string, startServer func(string)) error {
	model := NewModel(uploadsDir, startServer)
	p := tea.NewProgram(model, tea.WithAltScreen())
	_, err := p.Run()
	return err
}
