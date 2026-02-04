"""
N8N MCP Client Configuration
This script sets up MCP (Model Context Protocol) client for n8n
"""

import json
import os
from pathlib import Path

# N8N MCP 클라이언트 설정
MCP_CONFIG = {
    "mcpServers": {
        "n8n": {
            "command": "python",
            "args": ["-m", "n8n_mcp"],
            "env": {
                "N8N_HOST": "http://localhost:5678",
                "N8N_API_KEY": os.getenv("N8N_API_KEY", ""),
                "N8N_TIMEOUT": "30"
            }
        }
    }
}

# VS Code 설정
VSCODE_CONFIG = {
    "modelContext.enabled": True,
    "modelContext.servers": ["n8n"],
    "modelContext.n8n.host": "http://localhost:5678",
    "modelContext.n8n.apiKey": os.getenv("N8N_API_KEY", ""),
    "modelContext.autoConnect": True
}

def setup_mcp_config():
    """MCP 설정 파일 생성"""
    config_dir = Path.home() / ".config" / "mcp"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    config_file = config_dir / "n8n.json"
    with open(config_file, 'w') as f:
        json.dump(MCP_CONFIG, f, indent=2)
    
    print(f"✓ MCP 설정 파일 생성: {config_file}")
    return config_file

def get_vscode_settings():
    """VS Code 설정 반환"""
    return VSCODE_CONFIG

def test_connection():
    """n8n 연결 테스트"""
    import requests
    
    host = os.getenv("N8N_HOST", "http://localhost:5678")
    api_key = os.getenv("N8N_API_KEY", "")
    
    try:
        headers = {"X-N8N-API-KEY": api_key}
        response = requests.get(f"{host}/api/v1/workflows", headers=headers, timeout=5)
        
        if response.status_code == 200:
            print("✓ N8N 서버 연결 성공")
            return True
        else:
            print(f"✗ N8N 서버 연결 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 연결 오류: {e}")
        return False

if __name__ == "__main__":
    print("N8N MCP 클라이언트 설정 시작...\n")
    
    # 1. 환경 변수 확인
    n8n_host = os.getenv("N8N_HOST")
    n8n_api_key = os.getenv("N8N_API_KEY")
    
    if not n8n_api_key:
        print("⚠ N8N_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("다음 단계를 진행하세요:")
        print("1. http://localhost:5678 에서 n8n 웹 인터페이스 열기")
        print("2. Settings → API Keys → Create New API Key 클릭")
        print("3. API 키 복사 후 환경 변수 설정:")
        print("   export N8N_API_KEY='your_api_key_here'")
    
    # 2. MCP 설정 생성
    setup_mcp_config()
    
    # 3. VS Code 설정 출력
    print("\nVS Code settings.json에 다음을 추가하세요:")
    print(json.dumps(get_vscode_settings(), indent=2))
    
    # 4. 연결 테스트
    print("\n연결 테스트 중...")
    test_connection()
