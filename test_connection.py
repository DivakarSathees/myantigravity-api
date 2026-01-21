#!/usr/bin/env python3
"""
Test script to verify the MyAntigravity setup
"""

import asyncio
import json
from websockets import connect
import requests
from colorama import init, Fore, Style

init(autoreset=True)

SERVER_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/logs"

def print_status(message, status="info"):
    if status == "success":
        print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
    elif status == "error":
        print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
    elif status == "warning":
        print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}ℹ️  {message}{Style.RESET_ALL}")

async def test_websocket():
    """Test WebSocket connection"""
    print_status("Testing WebSocket connection...", "info")
    try:
        async with connect(WS_URL) as websocket:
            print_status("WebSocket connected successfully!", "success")
            
            # Wait for a message (with timeout)
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=2)
                data = json.loads(message)
                print_status(f"Received message: {data}", "success")
            except asyncio.TimeoutError:
                print_status("No messages received (this is normal)", "info")
            
            return True
    except Exception as e:
        print_status(f"WebSocket connection failed: {e}", "error")
        return False

def test_http_endpoints():
    """Test HTTP endpoints"""
    print_status("Testing HTTP endpoints...", "info")
    
    try:
        # Test health/root endpoint
        response = requests.get(f"{SERVER_URL}/docs")
        if response.status_code == 200:
            print_status("Server is running and accessible", "success")
        else:
            print_status(f"Server responded with status {response.status_code}", "warning")
        
        # Test log emission
        print_status("Testing log emission...", "info")
        response = requests.post(f"{SERVER_URL}/emit-test-log")
        if response.status_code == 200:
            print_status("Log emission endpoint working", "success")
        else:
            print_status(f"Log emission failed: {response.status_code}", "error")
        
        return True
    except requests.exceptions.ConnectionError:
        print_status("Cannot connect to server. Is it running?", "error")
        return False
    except Exception as e:
        print_status(f"HTTP test failed: {e}", "error")
        return False

def test_chat_endpoint():
    """Test the chat endpoint"""
    print_status("Testing chat endpoint...", "info")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/chat",
            json={"message": "Hello, agent! Please respond with 'Hello, human!'"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status(f"Agent responded: {data.get('response', 'No response')}", "success")
            return True
        else:
            print_status(f"Chat endpoint failed: {response.status_code}", "error")
            return False
    except Exception as e:
        print_status(f"Chat test failed: {e}", "error")
        return False

async def main():
    print("\n" + "="*60)
    print(f"{Fore.MAGENTA}🚀 MyAntigravity Connection Test{Style.RESET_ALL}")
    print("="*60 + "\n")
    
    # Test HTTP endpoints
    http_ok = test_http_endpoints()
    print()
    
    # Test WebSocket
    ws_ok = await test_websocket()
    print()
    
    # Test chat endpoint (only if HTTP is working)
    if http_ok:
        chat_ok = test_chat_endpoint()
    else:
        chat_ok = False
    
    print("\n" + "="*60)
    print(f"{Fore.MAGENTA}Test Results{Style.RESET_ALL}")
    print("="*60)
    print(f"HTTP Endpoints: {Fore.GREEN}✅ PASS{Style.RESET_ALL if http_ok else Fore.RED}❌ FAIL{Style.RESET_ALL}")
    print(f"WebSocket:      {Fore.GREEN}✅ PASS{Style.RESET_ALL if ws_ok else Fore.RED}❌ FAIL{Style.RESET_ALL}")
    print(f"Chat Endpoint:  {Fore.GREEN}✅ PASS{Style.RESET_ALL if chat_ok else Fore.RED}❌ FAIL{Style.RESET_ALL}")
    print("="*60 + "\n")
    
    if http_ok and ws_ok:
        print(f"{Fore.GREEN}🎉 All tests passed! Your setup is working correctly.{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Next steps:{Style.RESET_ALL}")
        print("1. Open VS Code")
        print("2. Press F5 in the extension folder to launch Extension Development Host")
        print("3. Open the MyAntigravity sidebar")
        print("4. Start chatting with your agent!\n")
    else:
        print(f"{Fore.RED}⚠️  Some tests failed. Please check the errors above.{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Troubleshooting:{Style.RESET_ALL}")
        print("1. Make sure the server is running: python3 server.py")
        print("2. Check if port 8000 is available")
        print("3. Verify your Azure OpenAI credentials in brain.py\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user{Style.RESET_ALL}")

