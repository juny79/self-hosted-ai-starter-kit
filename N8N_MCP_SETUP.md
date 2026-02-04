# N8N MCP 클라이언트 설정 가이드

## 개요
이 가이드는 VS Code에서 n8n MCP 클라이언트를 설정하는 방법을 설명합니다.

## 필수 사항
- n8n이 http://localhost:5678에서 실행 중
- VS Code 최신 버전
- Python 3.8 이상 (선택사항)

## 단계별 설정

### 1단계: N8N API 키 생성

1. 웹 브라우저에서 http://localhost:5678 열기
2. 초기 설정 완료 후 로그인
3. 우측 상단 메뉴 → **Settings** 클릭
4. **API Keys** 섹션으로 이동
5. **Create New API Key** 클릭
6. API 키 복사 및 안전한 장소에 저장

### 2단계: 환경 변수 설정

Windows PowerShell에서:
```powershell
$env:N8N_HOST = "http://localhost:5678"
$env:N8N_API_KEY = "your_api_key_here"
```

### 3단계: .env 파일 업데이트

프로젝트 루트의 `.env` 파일에 다음 추가:
```
N8N_API_KEY=your_api_key_here
```

### 4단계: VS Code 설정

1. VS Code에서 **Settings** (Ctrl+,) 열기
2. 다음 설정 추가:

```json
{
  "modelContext.enabled": true,
  "modelContext.servers": ["n8n"],
  "modelContext.n8n.host": "http://localhost:5678",
  "modelContext.n8n.apiKey": "${N8N_API_KEY}",
  "modelContext.autoConnect": true
}
```

또는 `.vscode/settings.json` 파일 직접 편집

### 5단계: MCP 클라이언트 설정 실행

Windows PowerShell에서:
```powershell
python n8n_mcp_setup.py
```

Linux/Mac에서:
```bash
python3 n8n_mcp_setup.py
```

### 6단계: VS Code 재시작

VS Code를 종료했다가 다시 열기

## 연결 확인

### MCP 상태 확인
1. VS Code 명령어 팔레트: Ctrl+Shift+P
2. "MCP: Show Status" 검색 및 실행
3. "n8n" 서버가 "Connected" 상태인지 확인

### N8N API 테스트
PowerShell에서:
```powershell
$headers = @{"X-N8N-API-KEY" = $env:N8N_API_KEY}
$response = Invoke-WebRequest -Uri "http://localhost:5678/api/v1/workflows" -Headers $headers
$response.StatusCode  # 200이면 성공
```

## 사용 가능한 기능

MCP 연결 후 다음을 수행할 수 있습니다:

- **Workflows 조회**: n8n에 저장된 모든 워크플로우 확인
- **Credentials 관리**: API 키 및 인증 정보 관리
- **Execution 모니터링**: 워크플로우 실행 상태 확인
- **Variables 관리**: 환경 변수 및 워크플로우 변수 설정
- **Nodes 검색**: n8n의 사용 가능한 노드 검색

## 문제 해결

### 연결 실패
- n8n이 실행 중인지 확인: http://localhost:5678 접속
- API 키 유효성 확인
- 환경 변수 설정 확인

### 권한 오류
- API 키가 올바른지 확인
- n8n에서 API 키 권한 설정 확인 (admin 권한 필요)

### VS Code 인식 안 됨
- `modelContext` 확장 설치 확인
- VS Code 캐시 삭제: `.vscode` 폴더 삭제 후 재시작

## 추가 리소스

- [N8N 문서](https://docs.n8n.io/)
- [MCP 프로토콜](https://modelcontextprotocol.io/)
- [VS Code MCP 확장](https://marketplace.visualstudio.com/items?itemName=anthropic.mcp)
