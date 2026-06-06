from server_base import create_server

mcp = create_server("Browser MCP Server", __file__)

if __name__ == "__main__":
    mcp.run()
