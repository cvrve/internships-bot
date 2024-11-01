#!/bin/bash

system_check() {
    case "$(uname)" in
        Darwin)
            echo "Mac OS X platform"
            if ! command -v brew &> /dev/null; then
                echo "Homebrew not found. Please install Homebrew."
                exit 1
            else
                brew install lsof
            fi
            ;;
        Linux)
            echo "GNU/Linux platform"
            if command -v apt &> /dev/null; then
                if ! command -v sudo &> /dev/null; then
                    echo "sudo command not found"
                    exit 1
                fi
                sudo apt update
                sudo apt install -y lsof python3 python3-pip python3-venv
            elif command -v dnf &> /dev/null; then
                if ! command -v sudo &> /dev/null; then
                    echo "sudo command not found"
                    exit 1
                fi
                sudo dnf install -y lsof python3 python3-pip python3-venv
            else
                echo "Neither apt nor dnf found. Please install required packages manually."
                exit 1
            fi
            ;;
        MINGW32_NT*|MINGW64_NT*)
            echo "Windows platform"
            if ! command -v choco &> /dev/null; then
                echo "Chocolatey command not found. Please install Chocolatey."
                exit 1
            else
                choco install lsof python
            fi
            ;;
        *)
            echo "Unsupported platform"
            exit 1
            ;;
    esac
}

checks() {
    if ! command -v python3 &> /dev/null; then
        echo "Python 3 not found"
        exit 1
    fi

    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    if [ -f "venv/bin/activate" ]; then
        echo "Activating virtual environment..."
        source venv/bin/activate
    else
        echo "Virtual environment activation script not found"
        exit 1
    fi

    if [ -f "requirements.txt" ]; then
        echo "Installing requirements..."
        python3 -m pip install --upgrade pip
        python3 -m pip install -r requirements.txt
    else
        echo "requirements.txt does not exist"
        exit 1
    fi
}

system_check
checks
