import os
from dotenv import load_dotenv

# Load the same .env your MCP server uses
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)

print("Playground starting...")

# 👉 Import whatever you want to debug
from tools.tags import retrieve_tag_by_name

def main():
    # Set a breakpoint on the next line
    result = retrieve_tag_by_name()  # use a real tag name here
    print("Result:", result)

if __name__ == "__main__":
    main()
