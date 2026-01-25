// Package qr provides QR code generation for Flashare.
package qr

import (
	"fmt"

	"os"

	"github.com/mdp/qrterminal/v3"
	"github.com/skip2/go-qrcode"
)

// PrintQRCode prints a QR code to the terminal.
func PrintQRCode(url string) {
	config := qrterminal.Config{
		Level:     qrterminal.L,
		Writer:    os.Stdout,
		BlackChar: qrterminal.WHITE,
		WhiteChar: qrterminal.BLACK,
		QuietZone: 1,
	}

	fmt.Println("  Scan to connect:")
	qrterminal.GenerateWithConfig(url, config)
}

// GeneratePNG generates a QR code as PNG bytes.
func GeneratePNG(url string, size int) ([]byte, error) {
	return qrcode.Encode(url, qrcode.Medium, size)
}

// GenerateString generates a QR code as a string (for testing).
func GenerateString(url string) string {
	q, err := qrcode.New(url, qrcode.Medium)
	if err != nil {
		return ""
	}
	return q.ToSmallString(false)
}
