# 뷰티컬리 쇼핑 에이전트 자동화 워크플로우 구축 가이드

## 📋 목차

1. [개요](#개요)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [필수 구성 요소](#필수-구성-요소)
4. [설치 및 설정](#설치-및-설정)
5. [워크플로우 구조](#워크플로우-구조)
6. [API 사용 방법](#api-사용-방법)
7. [트러블슈팅](#트러블슈팅)

## 개요

뷰티컬리 쇼핑 에이전트는 n8n을 기반으로 한 자동화 워크플로우로, 화장품 리뷰를 수집·분석하여 사용자에게 데이터 기반 추천을 제공합니다.

### 주요 기능

- **🤖 자동 리뷰 크롤링**: 매일 자정 뷰티컬리 리뷰 자동 수집
- **🧠 AI 감정 분석**: GPT-4o-mini를 활용한 리뷰 감정 분석
- **📊 ABSA 분석**: 속성별 감정 분석 (보습력, 흡수력, 향 등)
- **🔍 하이브리드 검색**: 키워드 검색 + 벡터 검색 결합
- **💡 전문가급 답변**: 실제 리뷰 데이터 기반 추천

## 시스템 아키텍처

```
┌─────────────────┐
│  사용자 요청    │
│  (Webhook)      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│      n8n Workflow Engine         │
│                                  │
│  ┌──────────────────────────┐  │
│  │ 1. 쿼리 분석 (GPT-4o)    │  │
│  └──────────┬───────────────┘  │
│             │                   │
│             ▼                   │
│  ┌─────────────────┐            │
│  │ 2. 임베딩 생성  │            │
│  └─────┬───────────┘            │
│        │                        │
│        ▼                        │
│  ┌──────────────┐  ┌─────────┐ │
│  │ Vector Search│  │Keyword  │ │
│  │  (Qdrant)    │  │Search   │ │
│  │              │  │(Postgres)│ │
│  └──────┬───────┘  └────┬────┘ │
│         │               │       │
│         └───────┬───────┘       │
│                 ▼               │
│  ┌──────────────────────────┐  │
│  │ 3. 결과 병합 & ABSA 집계 │  │
│  └──────────┬───────────────┘  │
│             │                   │
│             ▼                   │
│  ┌──────────────────────────┐  │
│  │ 4. 답변 생성 (GPT-4o)    │  │
│  └──────────┬───────────────┘  │
└─────────────┼───────────────────┘
              │
              ▼
      ┌───────────────┐
      │  JSON Response │
      └───────────────┘
```

### 데이터 흐름

1. **수집 파이프라인** (매일 자정 실행)
   - Kurly API → 리뷰 수집
   - GPT-4o-mini → 감정 분석 + ABSA
   - OpenAI Embedding → 벡터 생성
   - PostgreSQL + Qdrant → 저장

2. **쿼리 파이프라인** (실시간)
   - 사용자 질문 → 의도 파악
   - 하이브리드 검색 → 관련 리뷰 검색
   - ABSA 집계 → 속성별 통계
   - GPT-4o → 전문가급 답변 생성

## 필수 구성 요소

### 소프트웨어

- Docker & Docker Compose
- n8n (self-hosted)
- PostgreSQL 14+
- Qdrant Vector Database
- Ollama (선택사항)

### API 키

- OpenAI API Key (필수)
  - GPT-4o: 답변 생성
  - GPT-4o-mini: 분석
  - text-embedding-3-small: 벡터 생성

### 시스템 요구사항

- **최소**: 4GB RAM, 2 CPU cores
- **권장**: 8GB RAM, 4 CPU cores
- **디스크**: 20GB 이상 (벡터 데이터 저장)

## 설치 및 설정

### 1. 저장소 클론 및 환경 설정

```bash
git clone https://github.com/n8n-io/self-hosted-ai-starter-kit.git
cd self-hosted-ai-starter-kit

# 환경 변수 설정
cp .env.example .env
```

### 2. 환경 변수 편집 (.env)

```bash
# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-api-key

# PostgreSQL
POSTGRES_USER=n8n
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=n8n

# n8n
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your-admin-password
```

### 3. Docker Compose 실행

```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f n8n
```

### 4. PostgreSQL 스키마 적용

```bash
# PostgreSQL 컨테이너에 접속
docker-compose exec postgres psql -U n8n -d n8n

# 스키마 파일 실행
\i /path/to/database_schema.sql

# 또는 외부에서 실행
docker-compose exec -T postgres psql -U n8n -d n8n < database_schema.sql
```

### 5. Qdrant 초기화

```bash
# Python 스크립트 실행
python setup_qdrant.py

# 또는 수동으로 컬렉션 생성
curl -X PUT 'http://localhost:6333/collections/beauty_reviews' \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "size": 1536,
      "distance": "Cosine"
    }
  }'
```

### 6. n8n 워크플로우 임포트

1. 브라우저에서 `http://localhost:5678` 접속
2. 로그인 (위에서 설정한 인증 정보 사용)
3. **Workflows** → **Import from File**
4. `n8n/demo-data/workflows/workflow-beauty-kurly-shopping-agent.json` 선택
5. **Import** 클릭

### 7. 크리덴셜 설정

#### PostgreSQL Credential

1. **Settings** → **Credentials** → **Add Credential**
2. **PostgreSQL** 선택
3. 설정:
   - Host: `postgres`
   - Database: `n8n`
   - User: `n8n`
   - Password: (환경 변수에 설정한 값)
   - Port: `5432`

#### OpenAI Credential

1. **Settings** → **Credentials** → **Add Credential**
2. **OpenAI** 선택
3. API Key 입력

#### Slack Credential (선택사항)

1. **Settings** → **Credentials** → **Add Credential**
2. **Slack** 선택
3. OAuth Token 입력

### 8. 워크플로우 활성화

1. 임포트한 워크플로우 열기
2. 우측 상단 **Active** 스위치 켜기
3. **Schedule Trigger** 노드 확인 (매일 자정 실행)

## 워크플로우 구조

### 파이프라인 1: 리뷰 크롤링 & 분석

```
Schedule Trigger (자정)
  ↓
Get Product List (PostgreSQL)
  ↓
Split Products (배치 처리)
  ↓
Fetch Kurly Reviews (HTTP Request)
  ↓
Extract Review Data (Code)
  ↓
Check Duplicates (PostgreSQL)
  ↓
Filter New Reviews (IF)
  ↓
┌─────────────────────────┐
│ AI 분석 파이프라인      │
├─────────────────────────┤
│ 1. Sentiment Analysis   │
│    (GPT-4o-mini)        │
│         ↓               │
│ 2. ABSA Analysis        │
│    (GPT-4o-mini)        │
│         ↓               │
│ 3. Generate Embedding   │
│    (text-embedding)     │
└─────────────────────────┘
  ↓
Prepare Review Data (Code)
  ↓
Save to PostgreSQL
  ↓
Save to Qdrant
  ↓
Slack Notification
```

### 파이프라인 2: 사용자 쿼리 응답

```
Webhook (/beauty-query)
  ↓
Parse User Intent (GPT-4o-mini)
  ↓
┌────────────────┬────────────────┐
│ Generate Query │                │
│   Embedding    │                │
│       ↓        │                │
│ Vector Search  │ Keyword Search │
│   (Qdrant)     │  (PostgreSQL)  │
└────────┬───────┴────────┬───────┘
         │                │
         └────────┬───────┘
                  ↓
        Merge Search Results
                  ↓
        Aggregate ABSA Data
                  ↓
        Generate Final Answer
             (GPT-4o)
                  ↓
           Log Query
                  ↓
        Respond to Webhook
```

## API 사용 방법

### Webhook Endpoint

```
POST http://localhost:5678/webhook/beauty-query
```

### 요청 형식

```json
{
  "query": "건조한 피부에 좋은 토너 추천해줘",
  "user_id": "user123"
}
```

### 응답 형식

```json
{
  "success": true,
  "answer": "# 🎯 3줄 요약\n\n1. 건조한 피부에는 보습력이 우수한 '수분 가득 토너'를 추천드립니다...",
  "metadata": {
    "reviews_analyzed": 15,
    "avg_rating": 4.3,
    "avg_sentiment": 4.2,
    "absa_aspects": 7,
    "generated_at": "2026-02-04T10:30:00.000Z"
  }
}
```

### cURL 예제

```bash
curl -X POST http://localhost:5678/webhook/beauty-query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "지성 피부에 좋은 에센스 추천해줘",
    "user_id": "user456"
  }'
```

### Python 예제

```python
import requests

url = "http://localhost:5678/webhook/beauty-query"
payload = {
    "query": "민감성 피부를 진정시키는 제품 추천해줘",
    "user_id": "user789"
}

response = requests.post(url, json=payload)
result = response.json()

print(result['answer'])
```

## 주요 노드 설명

### 1. Sentiment Analysis (감정 분석)

**목적**: 리뷰의 전반적인 감정을 1-5점으로 평가

**프롬프트**:
```
당신은 화장품 리뷰 감정 분석 전문가입니다.

사용자 리뷰를 분석하여 다음을 JSON 형식으로 출력하세요:
{
  "sentiment_score": 1-5,
  "sentiment_label": "긍정" | "중립" | "부정",
  "emotions": ["기쁨", "실망"],
  "key_points": ["보습력 좋음", "끈적임"]
}
```

### 2. ABSA Analysis (속성별 감정 분석)

**목적**: 제품 속성별로 세밀한 감정 분석

**분석 속성**:
- 보습력 (hydration)
- 흡수력 (absorption)
- 끈적임 (stickiness)
- 향 (fragrance)
- 자극성 (irritation)
- 가성비 (value)
- 효과 (effectiveness)

### 3. Vector Search + Keyword Search (하이브리드 검색)

**벡터 검색** (가중치 0.6):
- 의미 기반 유사도 검색
- Qdrant cosine similarity
- threshold: 0.7 이상

**키워드 검색** (가중치 0.4):
- PostgreSQL ILIKE 검색
- 고평점 리뷰 우선
- 좋아요 순 정렬

### 4. Generate Final Answer (답변 생성)

**시스템 프롬프트**:
```
당신은 10년 경력의 뷰티 MD 출신 쇼핑 어드바이저입니다.

답변 구조:
1. 🎯 3줄 요약
2. 📊 데이터 기반 분석
3. 🔍 속성별 평가
4. ⚖️ 장단점
5. ⚠️ 주의사항
6. 💡 최종 판단
```

## 데이터베이스 스키마

### products 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL | 기본 키 |
| product_number | VARCHAR(50) | 제품 번호 (고유) |
| name | VARCHAR(255) | 제품명 |
| brand | VARCHAR(100) | 브랜드 |
| category | VARCHAR(100) | 카테고리 |
| price | DECIMAL(10,2) | 가격 |

### beauty_reviews 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL | 기본 키 |
| review_id | VARCHAR(100) | 리뷰 ID (고유) |
| product_number | VARCHAR(50) | 제품 번호 (외래 키) |
| content | TEXT | 리뷰 내용 |
| rating | DECIMAL(2,1) | 평점 (1-5) |
| sentiment_score | INTEGER | 감정 점수 (1-5) |
| sentiment_label | VARCHAR(20) | 감정 라벨 |
| absa_aspects | JSONB | ABSA 분석 결과 |
| skin_type | VARCHAR(50) | 피부 타입 |

### query_logs 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL | 기본 키 |
| user_id | VARCHAR(100) | 사용자 ID |
| query | TEXT | 사용자 질문 |
| answer | TEXT | 생성된 답변 |
| reviews_analyzed | INTEGER | 분석된 리뷰 수 |

## 성능 최적화

### 인덱싱 전략

```sql
-- PostgreSQL 인덱스
CREATE INDEX idx_reviews_product ON beauty_reviews(product_number);
CREATE INDEX idx_reviews_sentiment ON beauty_reviews(sentiment_score);
CREATE INDEX idx_reviews_rating ON beauty_reviews(rating DESC);
CREATE INDEX idx_reviews_absa_gin ON beauty_reviews USING GIN (absa_aspects);

-- Qdrant 페이로드 인덱스
PUT /collections/beauty_reviews/index
{
  "field_name": "sentiment_score",
  "field_schema": "integer"
}
```

### 배치 처리

- **Split Products 노드**: 한 번에 5개씩 처리
- **벡터 저장**: 배치로 삽입 (성능 향상)

### 캐싱

- 자주 검색되는 쿼리: Redis 캐싱 (선택사항)
- 제품 정보: 1시간 캐시

## 트러블슈팅

### 1. Qdrant 연결 오류

**증상**:
```
Connection refused: qdrant:6333
```

**해결**:
```bash
# Qdrant 컨테이너 상태 확인
docker-compose ps qdrant

# 재시작
docker-compose restart qdrant

# 로그 확인
docker-compose logs qdrant
```

### 2. PostgreSQL 권한 오류

**증상**:
```
permission denied for table beauty_reviews
```

**해결**:
```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO n8n;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO n8n;
```

### 3. OpenAI API 요청 제한

**증상**:
```
Rate limit exceeded
```

**해결**:
- API 키 확인 및 요금제 업그레이드
- 배치 크기 조정 (Split Products 노드)
- 요청 간 딜레이 추가

### 4. 임베딩 차원 불일치

**증상**:
```
Vector dimension mismatch
```

**해결**:
```python
# Qdrant 컬렉션 재생성
python setup_qdrant.py
# "y" 입력하여 기존 컬렉션 삭제 후 재생성
```

### 5. 메모리 부족

**증상**:
```
Container OOMKilled
```

**해결**:
```yaml
# docker-compose.yml 수정
services:
  n8n:
    mem_limit: 2g
    mem_reservation: 1g
```

## 모니터링

### 로그 확인

```bash
# n8n 로그
docker-compose logs -f n8n

# PostgreSQL 로그
docker-compose logs -f postgres

# Qdrant 로그
docker-compose logs -f qdrant
```

### 쿼리 성능 분석

```sql
-- 느린 쿼리 확인
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- 리뷰 통계
SELECT 
  COUNT(*) as total_reviews,
  AVG(sentiment_score) as avg_sentiment,
  COUNT(DISTINCT product_number) as products_with_reviews
FROM beauty_reviews;
```

### Qdrant 모니터링

```bash
# 컬렉션 정보
curl http://localhost:6333/collections/beauty_reviews

# 검색 성능 테스트
curl -X POST http://localhost:6333/collections/beauty_reviews/points/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ...],
    "limit": 10
  }'
```

## 확장 기능

### 1. 실시간 알림

Slack 노드를 추가하여 다음 이벤트 알림:
- 새로운 리뷰 수집 완료
- 부정적 리뷰 감지 (sentiment_score < 3)
- 일일 통계 리포트

### 2. 제품 추천 엔진

협업 필터링 추가:
- 유사 사용자 기반 추천
- 피부 타입별 맞춤 추천
- 구매 히스토리 기반 추천

### 3. 다국어 지원

번역 API 통합:
- 영어, 일본어, 중국어 리뷰 분석
- 다국어 답변 생성

### 4. 이미지 분석

Vision API 통합:
- 제품 이미지 분석
- 사용 전후 사진 비교

## 참고 자료

- [n8n Documentation](https://docs.n8n.io/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 라이선스

MIT License

## 기여

풀 리퀘스트를 환영합니다! 이슈를 먼저 열어주세요.

## 지원

문제가 발생하면 GitHub Issues에 등록해주세요.
