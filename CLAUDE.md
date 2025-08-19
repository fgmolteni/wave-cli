# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wave CLI is a Python-based command-line interface for managing LoRa (Long Range) radio communication devices. It provides an interactive terminal interface for sending/receiving messages, configuring radio parameters, and monitoring LoRa networks.

## Common Commands

### Development Commands
- `uv run main.py` - Run the CLI application
- `uv run main.py --interactive` - Start in interactive mode
- `uv install` - Install dependencies using uv package manager

### Interactive Mode Commands
The CLI supports an interactive mode with these commands:
- `send <message>` - Send LoRa message
- `listen` - Listen for incoming messages
- `config` - View/modify radio configuration
- `status` - Check module status
- `scan` - Scan frequency channels

## Code Architecture

### Core Structure
- `main.py` - Main CLI application with Click framework and Rich UI
- `constant/info.py` - Version information
- `cli/` - CLI modules directory (currently minimal)

### Key Components
- **Interactive Mode**: Full-featured terminal interface using Rich library for formatting
- **Configuration System**: Global config dict managing radio parameters (frequency, power, bandwidth, etc.)
- **Command Parser**: Uses shlex for parsing interactive commands with parameters
- **Rich UI**: Extensive use of Rich library for tables, progress bars, panels, and colored output

### Dependencies
- Click for CLI framework
- Rich for terminal UI and formatting
- Python 3.10+ required

### Application Flow
1. Entry point via Click CLI decorator
2. Banner display with Rich panels
3. Interactive mode loop with command parsing
4. Individual command handlers for LoRa operations
5. Simulated LoRa operations (no actual hardware integration yet)

The codebase is currently a prototype/simulation focusing on UI/UX design rather than actual LoRa hardware integration.