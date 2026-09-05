#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_NAME="YT Music Downloader"
APP_DIR="$DIR/$APP_NAME.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

echo "🔨 Building native macOS $APP_NAME.app..."

# Clean old bundle
rm -rf "$APP_DIR"

# Create standard macOS Bundle directories
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# Compile Native Swift Application Binary
swiftc "$DIR/main.swift" \
    -o "$MACOS_DIR/$APP_NAME" \
    -framework Cocoa \
    -framework WebKit \
    -O

# Copy resources
cp -r "$DIR/app" "$RESOURCES_DIR/"
if [ -f "$DIR/AppIcon.icns" ]; then
    cp "$DIR/AppIcon.icns" "$RESOURCES_DIR/"
fi

# Bundle standalone binaries (yt-dlp, ffmpeg, ffprobe) for Zero-Dependency Portable execution
BIN_DIR="$RESOURCES_DIR/bin"
mkdir -p "$BIN_DIR"
mkdir -p "$DIR/app/backend/bin"

for tool in yt-dlp ffmpeg ffprobe; do
    TOOL_PATH=$(which $tool || echo "/opt/homebrew/bin/$tool")
    if [ -f "$TOOL_PATH" ]; then
        cp "$TOOL_PATH" "$BIN_DIR/"
        cp "$TOOL_PATH" "$DIR/app/backend/bin/"
        chmod +x "$BIN_DIR/$tool"
        chmod +x "$DIR/app/backend/bin/$tool"
        echo "📦 Bundled $tool into app bundle"
    fi
done

# Create standard Info.plist
cat << EOF > "$CONTENTS_DIR/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.taichi.ytmusicdownloader</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>$APP_NAME</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0.0</string>
    <key>CFBundleVersion</key>
    <string>2</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsLocalNetworking</key>
        <true/>
    </dict>
</dict>
</plist>
EOF

chmod +x "$MACOS_DIR/$APP_NAME"

echo "✅ Native macOS App created successfully at: $APP_DIR"

# Package into Zero-Dependency Portable ZIP
PORTABLE_ZIP="$DIR/YT_Music_Downloader_macOS_Portable.zip"
rm -f "$PORTABLE_ZIP"
echo "📦 Packaging Zero-Dependency Portable ZIP archive..."
cd "$DIR" && zip -r -q "$PORTABLE_ZIP" "$APP_NAME.app"
echo "🎉 Standalone Portable Zip created at: $PORTABLE_ZIP"
