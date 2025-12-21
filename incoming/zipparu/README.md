# Zipparu

A Python tool to zip and upload folders filtered by .gitignore patterns.

## Installation and Usage

1. Clone the repo:

   ```bash
   git clone https://github.com/weholt/zipparu.git
   cd zipparu
   ```

2. Run setup:

   ```bat
   setup.bat
   ```

3. Add `~/.zipparu` with your API endpoint:

   ```
   API_URL=https://example.com/upload
   ```

4. Right-click inside any folder in Explorer → **Zipparu Upload**.
   
   It zips the folder (respecting `.gitignore`) and uploads to the API endpoint.

## Features

- Respects `.gitignore` patterns when creating zip files
- Windows Explorer integration via context menu
- Simple configuration via `~/.zipparu` file
- Command-line usage: `zipparu <folder_path>`