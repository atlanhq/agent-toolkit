# Windows Setup Guide (Without UV)

This guide provides step-by-step instructions for setting up the Atlan MCP server on Windows without using the UV package tool. This alternative installation method uses Python's built-in virtual environment capabilities.

## Prerequisites

- Python 3.11 or higher installed on your Windows machine
- PowerShell (comes with Windows)
- Access to your Atlan instance and API key

## Installation Steps

### Step 1 - Download the Code

1. Go to the following URL: https://github.com/atlanhq/agent-toolkit/tree/main
2. Click the green "Code" button and select "Download ZIP"
3. Download the ZIP file to your computer

### Step 2 - Setup the MCP Server Files

1. Extract the downloaded ZIP file
2. Rename the extracted folder to `agent-toolkit-main` 
3. Move the folder to `C:\agent-toolkit-main`

> **Important**: Please use this exact path and folder name so that the instructions in this guide will work properly.

### Step 3 - Setup Your Python Environment

1. Open PowerShell as Administrator (Right-click on PowerShell → "Run as Administrator")
2. Change to the modelcontextprotocol directory:
   ```powershell
   cd C:\agent-toolkit-main\modelcontextprotocol
   ```
3. Create a virtual environment in this directory:
   ```powershell
   python -m venv .venv
   ```

### Step 4 - Install the Required Libraries

1. Install the required libraries for this project:
   ```powershell
   C:\agent-toolkit-main\modelcontextprotocol\.venv\Scripts\python.exe -m pip install -e "C:\agent-toolkit-main\modelcontextprotocol\"
   ```

2. Verify the installation by running a quick test:
   ```powershell
   C:\agent-toolkit-main\modelcontextprotocol\.venv\Scripts\python.exe -c "import sys, fastmcp; print('OK via', sys.executable)"
   ```
   
   If successful, you should see: `OK via C:\agent-toolkit-main\modelcontextprotocol\.venv\Scripts\python.exe`

### Step 5 - Setup Claude Desktop to Use the Atlan MCP Server

1. Open Claude Desktop
2. Go to **Settings > Developer**
3. Click **Edit Config**. This will highlight the `claude_desktop_config.json` file
4. Open the file in a text editor like Notepad

The file should initially contain:
```json
{
  "mcpServers": {}
}
```

5. Replace the entire contents with:
```json
{
  "mcpServers": {
    "atlan": {
      "command": "C:\\agent-toolkit-main\\modelcontextprotocol\\.venv\\Scripts\\python.exe",
      "args": ["C:\\agent-toolkit-main\\modelcontextprotocol\\server.py"],
      "env": {
        "ATLAN_API_KEY": "YOUR_KEY",
        "ATLAN_BASE_URL": "https://YOUR_INSTANCE.atlan.com",
        "ATLAN_AGENT_ID": "PICK_NAME"
      }
    }
  }
}
```

6. **Configure your Atlan credentials**:
   - Replace `YOUR_KEY` with your actual Atlan API key
   - Replace `YOUR_INSTANCE` with your Atlan instance name
   - Replace `PICK_NAME` with your personal agent ID (can be anything like `My_Atlan_MCP`)

7. Save the file and **completely close Claude Desktop**
8. Reopen Claude Desktop

> **Troubleshooting**: If you get errors when reopening Claude, the JSON document may not be formatted correctly. This often happens with complex Atlan API keys. Copy your JSON text and use a JSON formatting tool or ask ChatGPT to help you format it correctly.

### Step 6 - Test Claude Integration

1. Open a new chat in Claude Desktop
2. Type: `"List all the Atlan MCP tools you have"`

   This should display all available tools. This confirms Claude knows about the tools but doesn't yet test the connection to Atlan.

3. Test the Atlan connection by typing: `"Using the Atlan MCP server, return to me a list of all the connections inside the instance"`

   This should return a list of all configured connections in your Atlan instance, proving that your connection to Atlan is working properly.

4. **Verify in Developer Settings**: Go back to Claude's Developer settings and you should now see your Atlan MCP Server listed.

**Congratulations! You now have a properly working Atlan MCP Server connected to Claude Desktop!**

### Step 7 - Setting up VSCode (Optional)

To install this MCP Server in VSCode:

1. Follow the official VSCode instructions: https://code.visualstudio.com/docs/copilot/customization/mcp-servers
2. Follow the "Add an MCP server to your workspace" instructions
3. When creating the `mcp.json` file, use the same configuration content that you used for Claude Desktop:

```json
{
  "mcpServers": {
    "atlan": {
      "command": "C:\\agent-toolkit-main\\modelcontextprotocol\\.venv\\Scripts\\python.exe",
      "args": ["C:\\agent-toolkit-main\\modelcontextprotocol\\server.py"],
      "env": {
        "ATLAN_API_KEY": "YOUR_KEY",
        "ATLAN_BASE_URL": "https://YOUR_INSTANCE.atlan.com",
        "ATLAN_AGENT_ID": "PICK_NAME"
      }
    }
  }
}
```

## Troubleshooting Common Issues

### Python Not Found
If you get a "Python not found" error, make sure Python 3.11+ is installed and added to your system PATH.

### Permission Errors
Run PowerShell as Administrator if you encounter permission errors during installation.

### JSON Configuration Errors
- Ensure your JSON is properly formatted
- Watch out for special characters in API keys that might break JSON formatting
- Use a JSON validator tool to check your configuration

### Virtual Environment Issues
If the virtual environment creation fails:
1. Make sure you're in the correct directory
2. Try using `python3` instead of `python` in the command

### Connection Test Failures
If Claude can see the tools but can't connect to Atlan:
- Verify your API key is correct and has proper permissions
- Check that your Atlan instance URL is correct
- Ensure your network allows connections to your Atlan instance
