# Flashare

VERSION ?= dev
COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "none")
DATE := $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")
LDFLAGS := -ldflags "-s -w -X main.version=$(VERSION) -X main.commit=$(COMMIT) -X main.date=$(DATE)"

.PHONY: all build clean install dev test

# Default target
all: build

# Build the binary
build:
	@echo "Building flashare..."
	@go build $(LDFLAGS) -o bin/flashare ./cmd/flashare

# Build for release (smaller binary)
release:
	@echo "Building release binary..."
	@CGO_ENABLED=0 go build $(LDFLAGS) -o bin/flashare ./cmd/flashare
	@upx --best bin/flashare 2>/dev/null || true

# Install to GOPATH/bin
install:
	@echo "Installing flashare..."
	@go install $(LDFLAGS) ./cmd/flashare

# Development build with race detector
dev:
	@go build -race $(LDFLAGS) -o bin/flashare ./cmd/flashare

# Run tests
test:
	@go test -v ./...

# Clean build artifacts
clean:
	@rm -rf bin/
	@go clean

# Tidy dependencies
tidy:
	@go mod tidy

# Download dependencies
deps:
	@go mod download

# Cross-compile for all platforms
cross:
	@echo "Building for multiple platforms..."
	@mkdir -p bin
	@GOOS=darwin GOARCH=amd64 go build $(LDFLAGS) -o bin/flashare-darwin-amd64 ./cmd/flashare
	@GOOS=darwin GOARCH=arm64 go build $(LDFLAGS) -o bin/flashare-darwin-arm64 ./cmd/flashare
	@GOOS=linux GOARCH=amd64 go build $(LDFLAGS) -o bin/flashare-linux-amd64 ./cmd/flashare
	@GOOS=linux GOARCH=arm64 go build $(LDFLAGS) -o bin/flashare-linux-arm64 ./cmd/flashare
	@GOOS=windows GOARCH=amd64 go build $(LDFLAGS) -o bin/flashare-windows-amd64.exe ./cmd/flashare
	@echo "Done! Binaries in bin/"

# Show help
help:
	@echo "Flashare Build Commands:"
	@echo "  make build    - Build binary"
	@echo "  make install  - Install to GOPATH/bin"
	@echo "  make dev      - Development build with race detector"
	@echo "  make release  - Optimized release build"
	@echo "  make cross    - Cross-compile for all platforms"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean build artifacts"
	@echo "  make tidy     - Tidy go.mod"
