#!/bin/bash
# Check if ffmpeg is installed and show helpful message if not

if command -v ffmpeg &> /dev/null; then
    echo "ffmpeg: OK"
    exit 0
else
    echo "ffmpeg: NOT FOUND"
    echo ""
    echo "The record feature requires ffmpeg for video processing."
    echo ""
    echo "Install ffmpeg:"
    echo "  macOS:   brew install ffmpeg"
    echo "  Ubuntu:  sudo apt install ffmpeg"
    echo "  Windows: choco install ffmpeg"
    echo ""
    echo "After installing, run the record command again."
    exit 1
fi
