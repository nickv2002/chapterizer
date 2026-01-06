.PHONY: build run-example test clean help

IMAGE_NAME := chapterize

help:
	@echo "Chapterize - Add AI-generated chapters to videos"
	@echo ""
	@echo "Available commands:"
	@echo "  make build           - Build the Docker image"
	@echo "  make run-example     - Run example with YouTube URL"
	@echo "  make test            - Test the tool with --help"
	@echo "  make clean           - Clean up generated files"
	@echo ""
	@echo "Quick start:"
	@echo "  make build"
	@echo "  make run-example"

build:
	@echo "🔨 Building Docker image..."
	docker build -t $(IMAGE_NAME) .
	@echo "✅ Build complete! Run 'make test' to verify."

test:
	@echo "🧪 Testing chapterize tool..."
	docker run --rm $(IMAGE_NAME)

run-example:
	@echo "▶️  Running chapterize on example YouTube video..."
	@echo "📹 Video: https://www.youtube.com/watch?v=pSSfzWw6lCw"
	docker run --rm -v "$(PWD):/app" $(IMAGE_NAME) \
		--url "https://www.youtube.com/watch?v=pSSfzWw6lCw" \
		--audio-only

clean:
	@echo "🧹 Cleaning up generated files..."
	rm -f FFMETADATA FFMETADATA-* aai-*.txt
	rm -f *.mp4.part
	@echo "✅ Cleanup complete!"

clean-all: clean
	@echo "🧹 Removing Docker image..."
	docker rmi $(IMAGE_NAME) 2>/dev/null || true
	@echo "✅ Full cleanup complete!"
