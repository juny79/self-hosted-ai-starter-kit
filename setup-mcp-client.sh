#!/bin/bash
# N8N MCP Client Setup Script

# N8N 서버가 http://localhost:5678에서 실행 중이어야 합니다.

# 1. n8n API 토큰 생성 (n8n 웹 인터페이스에서 수동으로 해야 함)
# http://localhost:5678 -> Settings -> API Keys -> Create New API Key

# 2. 환경 변수 설정
export N8N_HOST=http://localhost:5678
export N8N_API_KEY="your_api_key_here"

# 3. MCP 클라이언트 설치
npm install -g @modelcontextprotocol/n8n-mcp-client

# 4. MCP 서버 시작
mcp run n8n
