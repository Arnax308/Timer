#!/bin/bash

# Productivity Timer runner and installer script
# This script helps run and package the productivity timer

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="productivity-timer"
PYTHON_SCRIPT="portable_productivity_timer.py"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Function to check and install dependencies
check_dependencies() {
    echo "Checking dependencies..."
    
    # Check for pip
    if ! command -v pip3 &> /dev/null; then
        echo "pip3 is not installed. Installing pip..."
        sudo apt-get update
        sudo apt-get install -y python3-pip
    fi
    
    # Check for tkinter
    python3 -c "import tkinter" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "tkinter is not installed. Installing tkinter..."
        sudo apt-get update
        sudo apt-get install -y python3-tk
    fi
    
    # Check for notify2
    python3 -c "import notify2" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "notify2 is not installed. Installing notify2..."
        pip3 install notify2
    fi
    
    # Check for pyinstaller (only if we want to build executable)
    if [ "$1" == "build" ]; then
        python3 -c "import PyInstaller" 2>/dev/null
        if [ $? -ne 0 ]; then
            echo "PyInstaller is not installed. Installing PyInstaller..."
            pip3 install pyinstaller
        fi
    fi
    
    echo "All dependencies are installed."
}

# Function to run the application
run_app() {
    echo "Running Productivity Timer..."
    python3 "$SCRIPT_DIR/$PYTHON_SCRIPT"
}

# Function to build executable
build_executable() {
    echo "Building executable..."
    
    # Create a temporary directory for the build
    BUILD_DIR="$SCRIPT_DIR/build"
    mkdir -p "$BUILD_DIR"
    
    # Copy the icon if it exists
    if [ -f "$SCRIPT_DIR/timer_icon.png" ]; then
        cp "$SCRIPT_DIR/timer_icon.png" "$BUILD_DIR/"
    else
        echo "Warning: No icon file found (timer_icon.png). The application will use default icon."
    fi
    
    # Build the executable
    cd "$SCRIPT_DIR"
    pyinstaller --onefile --windowed --name "$APP_NAME" \
                --add-data "timer_icon.png:." \
                --distpath "$SCRIPT_DIR/dist" \
                --workpath "$BUILD_DIR" \
                "$PYTHON_SCRIPT"
    
    # Clean up
    rm -rf "$BUILD_DIR"
    rm -f "$SCRIPT_DIR/$APP_NAME.spec"
    
    echo "Executable created at: $SCRIPT_DIR/dist/$APP_NAME"
    echo "You can move this executable anywhere on your system."
    
    # Make executable
    chmod +x "$SCRIPT_DIR/dist/$APP_NAME"
    
    # Create desktop entry
    create_desktop_entry
}

# Function to create desktop entry
create_desktop_entry() {
    DESKTOP_FILE="$HOME/.local/share/applications/$APP_NAME.desktop"
    
    echo "Creating desktop entry..."
    mkdir -p "$HOME/.local/share/applications"
    
    echo "[Desktop Entry]" > "$DESKTOP_FILE"
    echo "Name=Productivity Timer" >> "$DESKTOP_FILE"
    echo "Comment=A productivity timer with notifications" >> "$DESKTOP_FILE"
    echo "Exec=$SCRIPT_DIR/dist/$APP_NAME" >> "$DESKTOP_FILE"
    echo "Terminal=false" >> "$DESKTOP_FILE"
    echo "Type=Application" >> "$DESKTOP_FILE"
    echo "Categories=Utility;" >> "$DESKTOP_FILE"
    
    if [ -f "$SCRIPT_DIR/timer_icon.png" ]; then
        # Copy icon to standard location
        mkdir -p "$HOME/.local/share/icons"
        cp "$SCRIPT_DIR/timer_icon.png" "$HOME/.local/share/icons/$APP_NAME.png"
        echo "Icon=$HOME/.local/share/icons/$APP_NAME.png" >> "$DESKTOP_FILE"
    fi
    
    chmod +x "$DESKTOP_FILE"
    echo "Desktop entry created. You can now find the application in your application menu."
}

# Main script logic
case "$1" in
    "run")
        check_dependencies
        run_app
        ;;
    "build")
        check_dependencies "build"
        build_executable
        ;;
    "install")
        check_dependencies
        if [ ! -f "$SCRIPT_DIR/dist/$APP_NAME" ]; then
            echo "Executable not found. Building first..."
            build_executable
        fi
        create_desktop_entry
        echo "Installation complete!"
        ;;
    *)
        echo "Usage: $0 [run|build|install]"
        echo "  run     - Run the productivity timer"
        echo "  build   - Build executable"
        echo "  install - Install desktop entry"
        ;;
esac

exit 0