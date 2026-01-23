#!/bin/bash

# Linux Ring Installer Script because the user wants to "distribute it"
# This moves the built dist folder to /opt and sets up the desktop entry

APP_NAME="LinuxRing"
INSTALL_DIR="/opt/$APP_NAME"
DESKTOP_FILE="LinuxRing.desktop"
SOURCE_DIST="dist/$APP_NAME" # Folder created by PyInstaller

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

echo "Installing $APP_NAME..."

# Check if build exists
if [ ! -d "$SOURCE_DIST" ]; then
    echo "Error: Build directory '$SOURCE_DIST' not found."
    echo "Please run: pyinstaller --noconfirm --onedir --windowed --name \"LinuxRing\" --add-data \"assets:assets\" --clean main.py"
    exit 1
fi

# Remove old install
if [ -d "$INSTALL_DIR" ]; then
    echo "Removing existing installation..."
    rm -rf "$INSTALL_DIR"
fi

# Copy files
echo "Copying files to $INSTALL_DIR..."
cp -r "$SOURCE_DIST" "$INSTALL_DIR"

# Install Desktop Entry
if [ -f "$DESKTOP_FILE" ]; then
    echo "Installing desktop shortcut..."
    cp "$DESKTOP_FILE" /usr/share/applications/
    chmod +x /usr/share/applications/"$DESKTOP_FILE"
else
    echo "Warning: $DESKTOP_FILE not found. Skipping shortcut creation."
fi

echo "Installation Complete!"
echo "You can now launch Linux Ring from your application menu."
