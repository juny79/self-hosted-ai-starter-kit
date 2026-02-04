# N8N MCP 연결 가이드 - 완료 단계

## ✅ 완료된 작업
- [x] Docker compose GPU-Nvidia 설정으로 실행 중
- [x] N8N 서버 시작 (http://localhost:5678)
- [x] MCP 설정 파일 생성
- [x] VS Code 설정 파일 생성

## 🔄 다음 단계 (필수)

### 1단계: N8N API 키 생성
1. 브라우저 열기: **http://localhost:5678**
2. 초기 설정 완료 (이메일, 비밀번호 설정)
3. 로그인
4. 우측 상단 메뉴 버튼 (☰) → **Settings** 클릭
5. 좌측 메뉴에서 **API Keys** 선택
6. **Create New API Key** 버튼 클릭
7. API 키 복사 (한 번만 표시됨)

### 2단계: 환경 변수 설정
PowerShell에서 다음 명령 실행:
```powershell
$env:N8N_API_KEY = "YOUR_API_KEY_HERE"
# 위 YOUR_API_KEY_HERE를 1단계에서 복사한 키로 교체
```

### 3단계: MCP 연결 구성

**선택지 A: VS Code 사용자 설정 (권장)**
1. VS Code 열기
2. `Ctrl+,` (또는 Settings 열기)
3. 검색: `modelContext`
4. 다음 설정 추가:
```json
{
  "modelContext.enabled": true,
  "modelContext.servers": ["n8n"],
  "modelContext.n8n.host": "http://localhost:5678",
  "modelContext.n8n.apiKey": "${N8N_API_KEY}",
  "modelContext.autoConnect": true
}
```

**또는 선택지 B: .vscode/settings.json 직접 편집**
파일 위치: `.vscode/settings.json`
이미 생성되어 있으니 필요시 업데이트

### 4단계: 연결 확인

**방법 1: PowerShell에서 API 테스트**
```powershell
$headers = @{"X-N8N-API-KEY" = $env:N8N_API_KEY}
$response = Invoke-WebRequest -Uri "http://localhost:5678/api/v1/workflows" -Headers $headers
Write-Host "상태: $($response.StatusCode)" # 200이면 성공
```

**방법 2: Python 스크립트로 테스트**
```powershell
python n8n_mcp_setup.py
```

**방법 3: VS Code MCP 상태 확인**
1. `Ctrl+Shift+P` (명령 팔레트)
2. "MCP: Show Status" 검색 및 실행
3. "n8n" 서버 상태 확인

## 🎯 MCP 연결 후 사용 가능한 기능

### N8N 워크플로우 관리
- 모든 워크플로우 목록 조회
- 워크플로우 상세 정보 확인
- 워크플로우 상태 모니터링

### 인증 정보 관리
- 저장된 Credentials 조회
- 새로운 API 키 관리

### 워크플로우 실행 모니터링
- 현재 실행 중인 작업 확인
- 실행 로그 확인
- 실행 결과 분석

### 환경 변수 관리
- 워크플로우 변수 설정
- 환경별 설정 관리

## 🐛 문제 해결

### "연결 거부" 오류
```
ConnectionRefusedError: [WinError 10061]
```
**해결책:**
- Docker Desktop 실행 확인
- `docker ps` 명령으로 컨테이너 상태 확인
- `docker compose --profile gpu-nvidia logs n8n` 으로 에러 로그 확인

### "Invalid API Key" 오류
**해결책:**
- API 키가 올바르게 복사되었는지 확인
- N8N 에서 새로운 API 키 생성
- 환경 변수 설정 재확인

### VS Code에서 MCP 인식 안 됨
**해결책:**
1. Anthropic MCP 확장 설치 확인
2. VS Code 재시작
3. `.vscode` 폴더 삭제 후 새로 생성

## 📋 체크리스트

- [ ] Docker compose 실행 중 (http://localhost:5678 접속 가능)
- [ ] N8N API 키 생성 완료
- [ ] 환경 변수 `N8N_API_KEY` 설정 완료
- [ ] VS Code MCP 설정 추가 완료
- [ ] 연결 테스트 성공 (상태 코드 200)
- [ ] VS Code에서 MCP 상태 "Connected" 확인

## 📞 추가 정보

### 중요 포트
- N8N: http://localhost:5678
- Ollama: http://localhost:11434
- Qdrant: http://localhost:6333
- PostgreSQL: localhost:5432

### 파일 위치
- 설정 파일: `.vscode/settings.json`
- MCP 설정: `~/.config/mcp/n8n.json`
- 환경 설정: `.env`

### 로그 확인
```powershell
# N8N 로그
docker compose logs -f n8n

# 모든 서비스 로그
docker compose logs -f
```

### 서비스 재시작
```powershell
# 특정 서비스 재시작
docker compose restart n8n

# 모든 서비스 재시작
docker compose --profile gpu-nvidia restart

# 서비스 중지
docker compose --profile gpu-nvidia down
```

---

**설정이 완료되면 이 파일을 삭제해도 좋습니다.**
