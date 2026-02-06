# 🔴 HTTP 404 오류 해결 가이드

## 문제

```
HTTP 404: The requested webhook "POST beauty-query" is not registered.
```

## 원인

**워크플로우가 활성화(Active)되지 않았습니다!**

n8n에서 워크플로우가 비활성 상태이면 Production Webhook이 등록되지 않습니다.

## ✅ 해결 방법 (5분 안에 완료)

### 1단계: n8n 웹 UI 접속

브라우저에서 열기:
```
http://localhost:5678
```

### 2단계: 로그인

기본 인증 정보 (.env 파일 확인):
- Username: `admin` (기본값)
- Password: .env 파일의 `N8N_BASIC_AUTH_PASSWORD` 값

### 3단계: 워크플로우 임포트

1. 좌측 메뉴에서 **"Workflows"** 클릭
2. 우측 상단 **"+ New"** → **"Import from File"** 클릭
3. 파일 선택: `n8n/demo-data/workflows/workflow-beauty-kurly-shopping-agent.json`
4. **"Import"** 클릭

### 4단계: Credentials 설정

워크플로우를 열면 credentials 설정이 필요합니다.

#### 4-1. PostgreSQL Credential

1. 빨간색으로 표시된 노드 클릭 (예: "Get Product List")
2. **"PostgreSQL account"** 옆 **"Create New"** 클릭
3. 입력:
   ```
   Name: PostgreSQL account
   Host: postgres
   Database: n8n
   User: n8n
   Password: (your .env POSTGRES_PASSWORD)
   Port: 5432
   ```
4. **"Save"** 클릭

#### 4-2. OpenAI Credential

1. OpenAI 노드 클릭 (예: "Sentiment Analysis")
2. **"OpenAI account"** 옆 **"Create New"** 클릭
3. **API Key** 입력
4. **"Save"** 클릭

#### 4-3. Slack Credential (선택사항)

1. "Slack Notification" 노드 클릭
2. Slack 연동하거나, 해당 노드 삭제

### 5단계: 워크플로우 활성화 ⭐ **중요!**

1. 우측 상단에 **"Active"** 토글 스위치 확인
2. 현재 **OFF** (회색)일 경우 → **ON** (파란색)으로 변경
3. **"Save"** 버튼 클릭

![](https://docs.n8n.io/assets/images/workflow-active-toggle-d7c8e0f7d0b7a0e0e0e0e0e0.png)

### 6단계: Webhook URL 확인

1. "User Query Webhook" 노드 클릭
2. **"Webhook URLs"** 섹션 확인
3. **Production URL** 복사:
   ```
   http://localhost:5678/webhook/beauty-query
   ```

### 7단계: 테스트 실행

PowerShell에서:
```powershell
python test_simple.py
```

또는:
```powershell
Invoke-WebRequest -Uri "http://localhost:5678/webhook/beauty-query" `
  -Method POST `
  -Body (@{query="건조한 피부 토너 추천"; user_id="test"} | ConvertTo-Json) `
  -ContentType "application/json"
```

## 🔍 추가 확인 사항

### 데이터베이스 스키마 확인

PostgreSQL 스키마가 적용되었는지 확인:

```powershell
docker-compose exec -T postgres psql -U n8n -d n8n -c "\dt"
```

테이블 목록에 다음이 있어야 합니다:
- `products`
- `beauty_reviews`
- `query_logs`

없다면:
```powershell
Get-Content database_schema.sql | docker-compose exec -T postgres psql -U n8n -d n8n
```

### Qdrant 확인

```powershell
Invoke-WebRequest -Uri "http://localhost:6333/collections/beauty_reviews"
```

컬렉션이 없다면:
```powershell
python setup_qdrant.py
```

## 📊 상태 확인 명령어

### 모든 서비스 상태
```powershell
docker-compose ps
```

모두 "Up" 상태여야 합니다.

### n8n 로그 확인
```powershell
docker-compose logs -f n8n
```

### PostgreSQL 연결 테스트
```powershell
docker-compose exec postgres psql -U n8n -d n8n -c "SELECT version();"
```

### Qdrant 상태
```powershell
Invoke-WebRequest -Uri "http://localhost:6333/"
```

## ❓ 여전히 404 오류?

### 체크리스트

- [ ] docker-compose ps에서 n8n이 "Up" 상태
- [ ] http://localhost:5678 접속 가능
- [ ] 워크플로우 임포트 완료
- [ ] PostgreSQL credential 설정 완료
- [ ] OpenAI credential 설정 완료
- [ ] 워크플로우 **Active 스위치 ON** (가장 중요!)
- [ ] 워크플로우 저장 완료
- [ ] 데이터베이스 스키마 적용 완료

### 완전 초기화 (최후의 수단)

```powershell
# 1. 모든 컨테이너 중지 및 삭제
docker-compose down -v

# 2. 재시작
docker-compose up -d

# 3. 데이터베이스 스키마 적용
Get-Content database_schema.sql | docker-compose exec -T postgres psql -U n8n -d n8n

# 4. Qdrant 초기화
python setup_qdrant.py

# 5. n8n UI에서 워크플로우 임포트 및 활성화
```

## 📞 추가 도움

1. [BEAUTY_KURLY_WORKFLOW_GUIDE.md](BEAUTY_KURLY_WORKFLOW_GUIDE.md) - 전체 가이드
2. [n8n 공식 문서](https://docs.n8n.io/)
3. n8n 실행 로그 확인: `docker-compose logs -f n8n`

---

**가장 중요한 것: 워크플로우 Active 스위치를 ON으로!** 🔥
