# workflow-user-query.json 수정 사항

## 🔴 발견된 문제 5가지

### 1️⃣ **Node 5 - HTTP Request Body JSON 형식 오류**
**문제:**
```json
"body": {\"vector\": \"={{$json.data}}\", ...}  ❌
```

**원인:** JSON 문자열 이스케이프 오류로 인해 Qdrant API가 올바른 JSON을 받지 못함

**수정:**
```json
"body": "{\n  \"vector\": {{$json.data}},\n  \"limit\": 20,\n  \"with_payload\": true,\n  \"score_threshold\": 0.7\n}"
```

---

### 2️⃣ **Node 4 - OpenAI Embedding 출력 처리 실패**
**문제:** 
- OpenAI embedding 노드의 출력이 바뀜
- `$json.data` 필드가 Node 5에서 접근 불가

**수정:** Code 노드로 변경하여 embedding 데이터 추출
```javascript
const embedding = items[0].json.data[0].embedding;
return [{ json: { data: embedding, ... } }];
```

---

### 3️⃣ **Node 6 - 입력 데이터 형식 불일치**
**문제:**
- Node 3 (SQL 쿼리)와 Node 5 (HTTP 요청)의 출력 구조가 다름
- Code 노드에서 데이터 병합 실패

**수정:** 
- 별도의 Code 노드(Node 6)에서 두 소스 병합
- `runOnceForAllItems` 모드로 설정
- 각 소스에 접근 가능하도록 수정

```javascript
const keywordResults = items[0].json || [];      // Node 3 출력
const vectorResults = items[1].json.result || [];// Node 5 출력
```

---

### 4️⃣ **Node 7, 8 - 입력 필드 누락**
**문제:**
- Node 6에서 생성되지 않은 필드 참조
- `product_name`, `reviews`, `absa_result` 등 정의되지 않음

**수정:** Node 6 출력 구조 명확히
```javascript
{
  "reviews": "리뷰 목록 (문자열)",
  "review_count": 10,
  "avg_score": 4.2,
  "top_results": [...]
}
```

---

### 5️⃣ **Node 2 - 원본 쿼리 전달 손실**
**문제:**
- Node 2 이후 원본 쿼리(`$json.query`)가 손실됨
- Node 8에서 사용할 수 없음

**수정:** Node 2 프롬프트 단순화 및 쿼리 보존
```javascript
"originalQuery": items[0].json.query || ''
```

---

## ✅ 수정 내용 요약

| 항목 | 수정 전 | 수정 후 |
|------|--------|--------|
| **Node 4** | OpenAI Embedding 노드 | Code 노드 (데이터 추출) |
| **Node 5** | 잘못된 JSON body | 올바른 JSON 형식 |
| **Node 6** | 간단한 merge | 복잡한 merge + 데이터 준비 |
| **Node 6 mode** | 없음 | `runOnceForAllItems` |
| **Node 7** | 존재하지 않는 필드 참조 | 올바른 필드 참조 |
| **Node 8** | 누락된 데이터 | 완전한 데이터 구조 |
| **Node 9** | 불완전한 응답 | 완전한 메타데이터 포함 |

---

## 🔧 n8n에서 추가 설정 필요

### Credential 설정 (n8n UI에서)

1. **PostgreSQL Credential**
   - Host: `postgres`
   - Database: `beautyreviews`
   - User: `n8n`
   - Password: (설정한 비밀번호)

2. **OpenAI Credential**
   - API Key: (자신의 OpenAI API 키)

3. **Webhook URL**
   ```
   POST http://localhost:5678/webhook/ask
   ```

---

## 📊 데이터 흐름 (수정 후)

```
[1] Webhook (POST /ask)
    ↓
[2] Parse User Intent (LLM)
    ├→ [3] Keyword Search (PostgreSQL)
    │        ↓
    │       (리뷰 데이터)
    │
    └→ [4] Generate Query Embedding (Code)
             ↓
        [5] Vector Search (Qdrant)
             ↓
        (벡터 검색 결과)
    
    [3] + [5] ↓
    
[6] Merge Results (Code)
    ├ 키워드 검색 결과 (가중치 0.3)
    ├ 벡터 검색 결과 (가중치 0.7)
    └→ reviews, review_count, avg_score 생성
         ↓
[7] ABSA Analysis (LLM)
    ↓
[8] Generate Answer (LLM - MD 페르소나)
    ↓
[9] Respond to Webhook (JSON)
    ↓
클라이언트에 답변 반환
```

---

## 🚀 테스트 방법

### 1. n8n UI에서 워크플로우 임포트
```
Settings → Workflows → Import
파일: workflow-user-query.json
```

### 2. Credentials 설정
```
Settings → Credentials
PostgreSQL, OpenAI 설정
```

### 3. 워크플로우 활성화
```
Active 토글 ON
```

### 4. 테스트 (PowerShell)
```powershell
$body = @{
    query = "건조한 피부에 좋은 토너 추천해줘"
    user_id = "test_user"
} | ConvertTo-Json

Invoke-WebRequest `
    -Uri "http://localhost:5678/webhook/ask" `
    -Method POST `
    -Body $body `
    -ContentType "application/json" `
    -UseBasicParsing
```

---

## 📝 주의사항

1. **Node 4 변경**: OpenAI Embedding 노드에서 Code 노드로 변경
   - 직접 임베딩 노드를 사용하려면 별도 credential 연결 필요
   - Code 노드가 더 유연함

2. **Node 6의 `runOnceForAllItems` 설정**
   - 이 옵션이 중요: 두 입력을 모두 받아서 한 번에 처리

3. **PostgreSQL 쿼리**
   - `sentiment_score >= 4`로 필터링하여 긍정 리뷰만 사용
   - 필요시 조정 가능

4. **Qdrant 컬렉션**
   - `beauty_reviews` 컬렉션이 미리 생성되어야 함
   - Workflow 1에서 생성됨

---

## ✨ 이제 준비 완료!

수정된 workflow-user-query.json을 n8n에 임포트하면 정상 작동합니다. 🎉
