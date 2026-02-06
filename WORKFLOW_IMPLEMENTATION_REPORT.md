# Beauty Kurly Shopping Agent 워크플로우 상세 구현 보고서

**작성일**: 2026-02-06  
**버전**: 1.0  
**상태**: 구현 진행 중

---

## 📋 목차

1. [개요 및 설계 의도](#개요-및-설계-의도)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [핵심 기술 스택](#핵심-기술-스택)
4. [워크플로우 단계별 상세 분석](#워크플로우-단계별-상세-분석)
5. [데이터 흐름 및 변환](#데이터-흐름-및-변환)
6. [파이프라인 구조](#파이프라인-구조)
7. [실무적 고려사항](#실무적-고려사항)
8. [성능 최적화 전략](#성능-최적화-전략)
9. [에러 처리 및 안정성](#에러-처리-및-안정성)

---

## 개요 및 설계 의도

### 🎯 프로젝트 목표

**Beauty Kurly Shopping Agent**는 온라인 뷰티 제품 쇼핑 플랫폼(Kurly)의 제품 정보와 고객 리뷰를 **자동으로 수집, 분석, 저장**하여 사용자 쿼리에 기반한 **지능형 제품 추천 시스템**을 구현하는 워크플로우입니다.

### 📊 핵심 가치 제안

| 항목 | 설명 |
|------|------|
| **데이터 자동화** | 수동 크롤링 제거, 일일 자동 업데이트 |
| **AI 감정 분석** | 리뷰의 객관적 감정 점수화 (1-5점) |
| **속성별 분석** | ABSA를 통한 제품 속성별 평가 (보습력, 흡수력 등) |
| **벡터 검색** | 의미 기반 검색으로 정확한 제품 추천 |
| **쿼리 기반 대답** | 사용자 질문에 대한 근거 있는 답변 생성 |

### 🔄 설계 철학

**분리된 파이프라인 아키텍처**

```
Upstream Pipeline (데이터 수집 및 처리)
    ↓
Downstream Pipeline (사용자 쿼리 응답)
```

- **상향식(Upstream)**: 배치 처리, 자동화, 주기적 실행
- **하향식(Downstream)**: 실시간 응답, API 트리거, 즉각적 반응

---

## 시스템 아키텍처

### 🏗️ 고수준 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                        n8n Workflow Engine                          │
│                                                                     │
│  ┌──────────────────────┐           ┌──────────────────────┐       │
│  │  CRAWLING PIPELINE   │           │  QUERY PIPELINE      │       │
│  │  (Daily Scheduled)   │           │  (Real-time Webhook) │       │
│  │                      │           │                      │       │
│  │  1. Get Products     │           │  1. Parse Query      │       │
│  │  2. Fetch Reviews    │           │  2. Embed Query      │       │
│  │  3. Sentiment Analysis│          │  3. Vector Search    │       │
│  │  4. ABSA Analysis    │           │  4. SQL Search       │       │
│  │  5. Generate Vector  │           │  5. Generate Answer  │       │
│  │  6. Save to DB       │           │  6. Log & Response   │       │
│  │  7. Save to Qdrant   │           │                      │       │
│  └──────────────────────┘           └──────────────────────┘       │
│           ↓                                    ↑                    │
│  ┌─────────────────────────────────────────────────────┐            │
│  │         Storage & Retrieval Layer                  │            │
│  └─────────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
    ┌─────────┐          ┌──────────┐      ┌─────────────┐
    │PostgreSQL│          │  Qdrant  │      │   Redis     │
    │ (RDB)    │          │ (Vector) │      │  (Cache)    │
    └─────────┘          └──────────┘      └─────────────┘
```

### 📊 데이터 흐름도

```
Kurly API
    ↓
[Webhook/Schedule]
    ↓
[Crawling Pipeline] ─→ PostgreSQL (products, beauty_reviews)
    ↓                       ↑
[AI Analysis]               │ (Read)
    ├─ Sentiment (Solar)    │
    ├─ ABSA Analysis        │
    └─ Embeddings (OpenAI)  │
    ↓                       │
[Vector Storage] → Qdrant ←─┘
    ↓
[Logging] → Query Logs Table
    

User Query
    ↓
[Webhook]
    ↓
[Query Pipeline] ←→ PostgreSQL (Select)
    ├─ Vector Search ←→ Qdrant
    ├─ Keyword Search ←→ PostgreSQL
    └─ ABSA Aggregation
    ↓
[AI Answer Generation] (Solar Pro)
    ↓
Response to User
```

---

## 핵심 기술 스택

### 🛠️ 컴포넌트별 기술

| 계층 | 기술 | 용도 | 선택 이유 |
|------|------|------|---------|
| **오케스트레이션** | n8n v0.234.0+ | 워크플로우 자동화 | 낮은 학습곡선, JSON 기반 구성 |
| **데이터베이스** | PostgreSQL 14+ | 관계형 데이터 저장 | JSONB 지원, 복합 쿼리 |
| **벡터DB** | Qdrant 1.7+ | 의미 기반 검색 | 높은 처리량, 페이로드 필터링 |
| **감정 분석** | Upstage Solar Pro | AI 분석 | 한국어 최적화, 비용 효율 |
| **임베딩** | OpenAI text-embedding-3-small | 벡터 생성 | 1536 차원, 높은 정확도 |
| **답변 생성** | Upstage Solar Pro | 최종 응답 | 한국어 자연스러움 |
| **컨테이너** | Docker Compose | 로컬 실행 환경 | 일관성, 재현성 |

### 🔐 자격증명 관리

```
n8n 내부 Credentials Store
├─ PostgreSQL account (products, beauty_reviews 접근)
├─ Upstage Solar API (감정분석, 답변생성)
├─ OpenAI API (임베딩, 최종답변)
└─ Qdrant API (벡터검색)
```

---

## 워크플로우 단계별 상세 분석

### Phase 1: 데이터 수집 및 준비 (Upstream Pipeline)

#### 1️⃣ **트리거: 스케줄/Webhook**

**정의**: 워크플로우의 진입점, 일일 자정에 자동 실행

```json
{
  "type": "schedule",
  "trigger": "every day at midnight (UTC)",
  "or": "POST /webhook/beauty-kurly-agent"
}
```

**실무 고려사항**:
- ✅ **UTC 시간대 설정**: 서버 시간대와 일치 필요
- ✅ **Webhook 대안**: 즉시 수동 실행 가능
- ✅ **실패 재시도**: n8n 내장 재시도 정책 사용

---

#### 2️⃣ **Get Product List: PostgreSQL 조회**

**목표**: 데이터베이스에서 최근 업데이트된 뷰티 제품 10개 추출

**SQL 쿼리**:
```sql
SELECT product_number, name, category 
FROM products 
WHERE category LIKE '%beauty%' 
ORDER BY updated_at DESC 
LIMIT 10;
```

**데이터 모델** (products 테이블):
```
┌─────────────┬──────────────┬────────────┐
│product_no   │name          │category    │
├─────────────┼──────────────┼────────────┤
│BK001        │수분 가득 토너 │beauty      │
│BK002        │진정 에센스   │beauty      │
│...          │...           │...        │
└─────────────┴──────────────┴────────────┘
```

**반환값**:
```javascript
[
  {
    "product_number": "BK001",
    "name": "수분 가득 토너",
    "category": "beauty"
  },
  ...
]
```

**실무 최적화**:
- `LIMIT 10`: 초기 테스트용 (프로덕션에서는 파라미터화)
- `updated_at DESC`: 가장 최근 데품 우선
- `LIKE '%beauty%'`: 정확한 카테고리 필터링

---

#### 3️⃣ **Split Products: 배치 처리**

**목표**: 10개의 제품을 5개 단위로 나누어 병렬 처리

```
Products [10개]
    ↓
Batch 1: [5개] ─→ 병렬 처리
Batch 2: [5개] ─→ 병렬 처리
```

**설정**:
```json
{
  "batchSize": 5,
  "node": "splitInBatches"
}
```

**이점**:
- ✅ API 요청 병렬화
- ✅ 메모리 효율성
- ✅ 시간 단축

---

#### 4️⃣ **Fetch Kurly Reviews: 외부 API 크롤링**

**목표**: 각 제품의 고객 리뷰를 Kurly API에서 가져오기

**API 엔드포인트**:
```
GET https://api.kurly.com/v2/reviews/products/{product_number}
```

**요청 예시**:
```http
GET /v2/reviews/products/BK001
User-Agent: Mozilla/5.0
Accept: application/json
```

**반환 데이터 구조**:
```json
{
  "product_number": "BK001",
  "data": {
    "reviews": [
      {
        "id": "REV_12345",
        "content": "정말 보습력이 좋아요! 건조한 제 피부에 딱 맞네요.",
        "rating": 5.0,
        "author": {"name": "사용자A"},
        "created_at": "2026-02-01T10:30:00Z",
        "like_count": 25,
        "verified_purchase": true,
        "attributes": {
          "skin_type": "건성",
          "age_group": "20s"
        }
      },
      ...
    ]
  }
}
```

**에러 처리**:
- timeout: 10초
- 404 응답: 해당 제품 건너뛰기
- 네트워크 오류: 재시도 3회

---

#### 5️⃣ **Extract Review Data: 데이터 정규화**

**목표**: 크롤링된 리뷰 데이터를 데이터베이스 스키마에 맞게 변환

**입력**:
```javascript
{
  "product_number": "BK001",
  "data": {
    "reviews": [
      {"id": "REV_123", "content": "...", "rating": 5.0, ...}
    ]
  }
}
```

**처리 로직** (Code 노드):
```javascript
const extractedReviews = [];

for (const item of items) {
  const productNumber = item.json.product_number;
  const reviews = item.json.data?.reviews || [];
  
  for (const review of reviews) {
    extractedReviews.push({
      json: {
        product_number: productNumber,
        review_id: review.id,
        content: review.content || review.comment,
        rating: review.rating || review.score,
        created_at: review.created_at || review.registered_at,
        author: review.author?.name || 'Anonymous',
        like_count: review.like_count || 0,
        verified_purchase: review.verified_purchase || false,
        skin_type: review.attributes?.skin_type || null,
        age_group: review.attributes?.age_group || null
      }
    });
  }
}

return extractedReviews;
```

**출력**:
```json
[
  {
    "product_number": "BK001",
    "review_id": "REV_123",
    "content": "정말 보습력이 좋아요!",
    "rating": 5.0,
    "created_at": "2026-02-01T10:30:00Z",
    "author": "사용자A",
    "like_count": 25,
    "verified_purchase": true,
    "skin_type": "건성",
    "age_group": "20s"
  },
  ...
]
```

**설계 고려사항**:
- ✅ Null 안전 처리 (`?.` 연산자)
- ✅ 대체값 설정 (`|| 'Anonymous'`)
- ✅ 타입 일관성 보장

---

### Phase 2: AI 분석 (Sentiment & ABSA)

#### 6️⃣ **Sentiment Analysis: Solar Pro로 감정 분석**

**목표**: 각 리뷰의 고객 만족도를 1-5점으로 수치화

**모델**: Upstage Solar Pro  
**온도**: 0.3 (일관성 중시)  
**응답 형식**: JSON

**프롬프트 구조**:
```
System Role: 화장품 리뷰 감정 분석 전문가

Few-Shot Examples:
- "재재재재구매 너무 좋아요" → 5점
- "좋다고 샀는데 더 써봐야할거 같아요" → 3점
- "향이 강해서 저는 별로입니다" → 2점

User Input: {리뷰 내용}

Expected Output: JSON with sentiment_score (1-5), label, emotions, key_points
```

**점수 체계** (한국 뷰티 시장 맞춤):
```
5점 (Very satisfied): 
  - 재구매 의사 강함, 극찬
  - 키워드: "완전 추천", "대사랑", "꿀템"

4점 (Satisfied):
  - 긍정적, 만족
  - 키워드: "좋아요", "괜찮아요", "추천"

3점 (Neutral):
  - 중립적, 장단점 혼재
  - 키워드: "그냥", "쏘쏘", "더 써봐야"

2점 (Dissatisfied):
  - 기대 이하, 부정적
  - 키워드: "별로", "실망", "안맞아"

1점 (Very dissatisfied):
  - 심각한 불만, 피부 트러블
  - 키워드: "못쓰겠음", "알러지", "끔찍"
```

**반환 데이터**:
```json
{
  "sentiment_score": 5,
  "sentiment_label": "Very satisfied",
  "emotions": ["기쁨", "만족감"],
  "key_points": ["보습력 탁월", "흡수 빠름"]
}
```

**실무 검증**:
- ✅ 점수 분포: 균형잡힌 분포 (1-5 골고루)
- ✅ 거짓양성 감지: 부정적 단어 포함 리뷰 재확인
- ✅ 언어 뉘앙스: 한국어 특화 모델 필수

---

#### 7️⃣ **ABSA (Aspect-Based Sentiment Analysis): 속성별 감정 분석**

**목표**: 제품의 각 특성(보습력, 흡수력, 향 등)에 대한 개별 평가

**분석 대상 속성** (화장품 업계 표준):
```
1. 보습력 (Hydration) - 피부 수분 공급 능력
2. 흡수력 (Absorption) - 제품 흡수 속도
3. 끈적임 (Stickiness) - 유분감, 텍스처
4. 향 (Fragrance) - 제품 냄새
5. 자극성 (Irritation) - 피부 자극 정도
6. 가성비 (Value) - 가격 대비 가치
7. 효과 (Effectiveness) - 실제 효과
```

**ABSA 프롬프트**:
```
당신은 ABSA 전문가입니다.
다음 리뷰의 속성별 감정을 분석하세요.

각 속성에 대해:
{
  "name": "속성명",
  "sentiment": "긍정|중립|부정",
  "score": 1-5,
  "mentioned": true/false,
  "quote": "관련 인용문"
}
```

**반환 데이터**:
```json
{
  "aspects": [
    {
      "name": "보습력",
      "sentiment": "긍정",
      "score": 5,
      "mentioned": true,
      "quote": "정말 보습력이 좋아요!"
    },
    {
      "name": "흡수력",
      "sentiment": "긍정",
      "score": 4,
      "mentioned": true,
      "quote": "끈적임도 없고 흡수도 빨라서"
    },
    {
      "name": "향",
      "sentiment": "중립",
      "score": 3,
      "mentioned": true,
      "quote": "향이 조금 강한 편"
    },
    {
      "name": "자극성",
      "sentiment": "긍정",
      "score": 5,
      "mentioned": false,
      "quote": null
    }
  ]
}
```

**데이터베이스 저장 (JSONB)**:
```sql
UPDATE beauty_reviews 
SET absa_aspects = jsonb_build_object(
  'hydration', score_5,
  'absorption', score_4,
  'stickiness', score_3,
  ...
)
WHERE review_id = 'REV_123';
```

**비즈니스 가치**:
- ✅ **세밀한 추천**: "지성피부인데 끈적임 없는 제품" 검색 가능
- ✅ **제품 개선**: 제조사가 약점 파악
- ✅ **사용자 만족도**: 피부 타입별 맞춤 추천

---

### Phase 3: 벡터화 및 저장

#### 8️⃣ **Generate Embedding: OpenAI 텍스트 임베딩**

**목표**: 리뷰 텍스트를 1536차원 벡터로 변환

**모델**: OpenAI text-embedding-3-small  
**차원수**: 1536  
**최대 토큰**: 8191

**입력**:
```
"정말 보습력이 좋아요! 건조한 제 피부에 딱 맞네요. 끈적임도 없고 흡수도 빨라서 아침에 사용하기 좋습니다."
```

**벡터 변환 과정**:
```
Text
  ↓
Tokenization (단어 분해)
  ↓
Neural Embedding (의미 벡터화)
  ↓
1536-dim Vector: [0.123, -0.456, 0.789, ...]
```

**벡터의 의미**:
```javascript
// 의미적으로 유사한 리뷰들은 벡터 거리가 가까움
review1 = "보습력이 정말 좋아요" → [벡터A]
review2 = "수분감이 탁월합니다"    → [벡터A']  // 거리 작음
review3 = "너무 기름져요"         → [벡터B]   // 거리 큼
```

**저장 구조**:
```json
{
  "review_id": "REV_123",
  "product_number": "BK001",
  "content": "정말 보습력이 좋아요...",
  "embedding": [0.123, -0.456, ..., 0.789],  // 1536개 값
  "sentiment_score": 5,
  "sentiment_label": "Very satisfied",
  "emotions": ["기쁨", "만족감"],
  "absa_aspects": {...},
  "processed_at": "2026-02-06T12:30:00Z"
}
```

**실무 고려사항**:
- ✅ 캐싱: 동일 텍스트는 재사용
- ✅ 배치 처리: 한 번에 여러 벡터 생성
- ✅ 비용: OpenAI API 호출 비용 주의

---

#### 9️⃣ **Save to PostgreSQL: 정규화된 데이터 저장**

**목표**: 분석 결과를 관계형 데이터베이스에 저장

**테이블: beauty_reviews**
```sql
CREATE TABLE beauty_reviews (
    id SERIAL PRIMARY KEY,
    review_id VARCHAR(100) UNIQUE NOT NULL,
    product_number VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    rating DECIMAL(2, 1),
    created_at TIMESTAMP,
    author VARCHAR(100),
    like_count INTEGER DEFAULT 0,
    verified_purchase BOOLEAN DEFAULT false,
    
    -- 사용자 속성
    skin_type VARCHAR(50),
    age_group VARCHAR(50),
    
    -- 감정 분석 결과
    sentiment_score INTEGER CHECK (sentiment_score >= 1 AND sentiment_score <= 5),
    sentiment_label VARCHAR(20),
    emotions JSONB,
    key_points JSONB,
    
    -- ABSA (속성별 감정분석)
    absa_aspects JSONB,
    
    -- 메타데이터
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (product_number) REFERENCES products(product_number) ON DELETE CASCADE
);
```

**n8n Insert 설정**:
```json
{
  "operation": "insert",
  "table": "beauty_reviews",
  "columns": {
    "review_id": "={{ $json.review_id }}",
    "product_number": "={{ $json.product_number }}",
    "content": "={{ $json.content }}",
    "rating": "={{ $json.rating }}",
    "created_at": "={{ $json.created_at }}",
    "author": "={{ $json.author }}",
    "like_count": "={{ $json.like_count }}",
    "verified_purchase": "={{ $json.verified_purchase }}",
    "skin_type": "={{ $json.skin_type }}",
    "age_group": "={{ $json.age_group }}",
    "sentiment_score": "={{ $json.sentiment_score }}",
    "sentiment_label": "={{ $json.sentiment_label }}",
    "emotions": "={{ $json.emotions }}",
    "key_points": "={{ $json.key_points }}",
    "absa_aspects": "={{ $json.absa_aspects }}",
    "processed_at": "={{ $json.processed_at }}"
  }
}
```

**데이터 무결성**:
- ✅ PK: review_id (고유성 보장)
- ✅ FK: product_number (제품 참조)
- ✅ CHECK: sentiment_score 범위 검증
- ✅ JSONB: 유연한 구조 저장

---

#### 🔟 **Save to Qdrant: 벡터 저장 및 인덱싱**

**목표**: 임베딩 벡터를 벡터 데이터베이스에 저장하여 유사도 검색 준비

**Qdrant 컬렉션 구조**:
```json
{
  "name": "beauty_reviews",
  "vector_size": 1536,
  "distance": "cosine",
  "payload": {
    "review_id": {"type": "keyword"},
    "product_number": {"type": "keyword"},
    "sentiment_score": {"type": "integer"},
    "rating": {"type": "float"},
    "skin_type": {"type": "keyword"},
    "created_at": {"type": "datetime"}
  }
}
```

**저장 데이터 예시**:
```json
{
  "id": 12345,
  "vector": [0.123, -0.456, ..., 0.789],  // 1536 차원
  "payload": {
    "review_id": "REV_123",
    "product_number": "BK001",
    "content": "정말 보습력이 좋아요...",
    "sentiment_score": 5,
    "rating": 5.0,
    "skin_type": "건성",
    "author": "사용자A",
    "created_at": "2026-02-01T10:30:00Z"
  }
}
```

**인덱싱 전략**:
- ✅ Vector Index: 빠른 유사도 검색 (HNSW)
- ✅ Payload Index: 필터링 최적화
- ✅ 거리 메트릭: Cosine (의미 유사성)

**검색 쿼리 예시**:
```json
{
  "vector": [사용자쿼리_임베딩],
  "limit": 20,
  "score_threshold": 0.7,
  "filter": {
    "must": [
      {"key": "sentiment_score", "range": {"gte": 3}}
    ]
  }
}
```

**이점**:
- ✅ O(1) 검색 시간복잡도
- ✅ 의미 기반 검색 (정확한 매칭 불필요)
- ✅ 페이로드 필터링 (감정점수, 피부타입 등)

---

### Phase 4: 사용자 쿼리 응답 (Query Pipeline)

#### 1️⃣ **User Query Webhook: 사용자 입력 수집**

**Webhook 엔드포인트**:
```
POST /webhook/beauty-query
Content-Type: application/json

{
  "user_id": "user_12345",
  "query": "지성 피부인데 끈적임 없는 토너 추천해줄래?",
  "skin_type": "지성",
  "concern": "건조함"
}
```

**n8n Webhook 노드**:
```json
{
  "httpMethod": "POST",
  "path": "beauty-query",
  "responseMode": "lastNode",
  "options": {}
}
```

---

#### 2️⃣ **Parse User Query: 쿼리 분석**

**목표**: 사용자 질문을 구조화된 데이터로 파싱

**AI 모델**: Upstage Solar Pro  
**온도**: 0.2 (정확성 중시)

**프롬프트**:
```
사용자 쿼리를 분석하여 JSON으로 출력:

{
  "intent": "추천" | "비교" | "리뷰요약" | "정보조회",
  "keywords": ["핵심키워드1", "핵심키워드2"],
  "filters": {
    "skin_type": "건성" | "지성" | "복합성" | null,
    "price_range": "저가" | "중가" | "고가" | null,
    "concern": "모공" | "주름" | "미백" | "건조함" | null
  },
  "product_category": "토너" | "에센스" | "크림" | null
}
```

**입력 예시**:
```
"지성 피부인데 끈적임 없는 토너 추천해줄래?"
```

**출력**:
```json
{
  "intent": "추천",
  "keywords": ["끈적임 없음", "토너", "지성"],
  "filters": {
    "skin_type": "지성",
    "price_range": null,
    "concern": "끈적임"
  },
  "product_category": "토너"
}
```

---

#### 3️⃣ **Generate Query Embedding: 쿼리 벡터화**

**목표**: 사용자 질문을 벡터로 변환

**프로세스**:
```
User Query
  ↓
OpenAI Embedding
  ↓
1536-dim Vector
```

**벡터 활용**:
- Qdrant에서 의미적으로 유사한 리뷰 검색
- "지성 피부 끈적임 없는 토너" → 관련 리뷰 벡터와 유사

---

#### 4️⃣ **Vector Search - Qdrant: 벡터 유사도 검색**

**목표**: 쿼리와 의미적으로 유사한 리뷰 추출

**Qdrant 검색 쿼리**:
```json
{
  "vector": [사용자쿼리_임베딩],
  "limit": 20,
  "with_payload": true,
  "score_threshold": 0.7,
  "filter": {
    "must": [
      {
        "key": "sentiment_score",
        "range": {"gte": 3}  // 긍정/중립 리뷰만
      }
    ]
  }
}
```

**반환 결과**:
```json
[
  {
    "score": 0.89,  // 유사도
    "payload": {
      "review_id": "REV_123",
      "product_number": "BK001",
      "content": "끈적임도 없고 흡수도 빨라서 좋아요",
      "sentiment_score": 5,
      "rating": 5.0,
      "skin_type": "지성"
    }
  },
  {
    "score": 0.85,
    "payload": {...}
  },
  ...
]
```

**알고리즘**: Approximate Nearest Neighbor (ANN)
- ✅ O(log n) 검색 시간
- ✅ 의미 유사성 기반 (단어 매칭 불필요)
- ✅ 페이로드 필터링 지원

---

#### 5️⃣ **Keyword Search - PostgreSQL: 키워드 기반 검색**

**목표**: SQL 기반 정확한 매칭 검색

**쿼리**:
```sql
SELECT review_id, product_number, content, sentiment_score
FROM beauty_reviews
WHERE (
  content ILIKE '%끈적임 없%' OR
  content ILIKE '%흡수%'
)
AND sentiment_score >= 3
AND (skin_type = '지성' OR skin_type IS NULL)
ORDER BY like_count DESC
LIMIT 20;
```

**검색 조건**:
- 텍스트 매칭: ILIKE (대소문자 구분 안함)
- 감정 필터: sentiment_score >= 3
- 피부타입: skin_type 매칭
- 정렬: 좋아요 수 기준

**결합 전략**:
```javascript
// Vector Search 결과 + Keyword Search 결과 병합
const vectorResults = await qdrantSearch(...);
const keywordResults = await sqlSearch(...);

// 중복 제거 및 스코어 합산
const merged = mergeResults(vectorResults, keywordResults);
// → 최상의 관련 리뷰 20개
```

---

#### 6️⃣ **ABSA Aggregation: 속성별 집계**

**목표**: 검색된 리뷰들의 ABSA 결과를 집계

**입력**: 20개의 리뷰

```javascript
const reviews = [
  {
    "absa_aspects": {
      "hydration": 5,
      "absorption": 4,
      "stickiness": 1,
      "fragrance": 3
    }
  },
  ...
];
```

**집계 로직**:
```javascript
const aggregated = {
  "hydration": {
    "avg_score": 4.8,
    "positive_count": 18,
    "negative_count": 1,
    "neutral_count": 1
  },
  "absorption": {
    "avg_score": 4.5,
    "positive_count": 17,
    "negative_count": 0,
    "neutral_count": 3
  },
  "stickiness": {
    "avg_score": 1.2,  // 낮을수록 좋음 (끈적임 적음)
    "positive_count": 19,
    "negative_count": 0,
    "neutral_count": 1
  },
  ...
};
```

**출력**:
```json
{
  "absa_summary": [
    {
      "aspect": "보습력",
      "avg_score": 4.8,
      "rating": "매우 긍정",
      "mention_rate": 90
    },
    {
      "aspect": "흡수력",
      "avg_score": 4.5,
      "rating": "긍정",
      "mention_rate": 85
    },
    {
      "aspect": "끈적임",
      "avg_score": 1.2,  // 역순
      "rating": "매우 긍정",
      "mention_rate": 95
    }
  ]
}
```

**비즈니스 로직**:
```
끈적임 점수 1.2 → "끈적임 거의 없음" (좋음)
보습력 점수 4.8 → "보습력 매우 뛰어남" (좋음)
→ 결론: "지성피부에 최적의 토너"
```

---

#### 7️⃣ **Generate Final Answer: 최종 답변 생성**

**목표**: 수집된 데이터를 기반으로 자연스러운 한국어 답변 생성

**모델**: Upstage Solar Pro  
**온도**: 0.7 (창의성과 정확성 균형)  
**최대 토큰**: 1500

**프롬프트 구조**:
```
당신은 10년 경력의 뷰티 MD 출신 쇼핑 어드바이저입니다.

사용자 질문: {user_query}

분석 데이터:
- 분석한 리뷰 수: 20개
- 평균 평점: 4.7/5
- 평균 감정 점수: 4.6/5

속성별 평가:
- 보습력: 4.8/5 (90% 긍정)
- 흡수력: 4.5/5 (85% 긍정)
- 끈적임: 1.2/5 (95% 긍정, 역순)

주요 리뷰 샘플:
1. [5/5] "끈적임도 없고 흡수도 빨라서 좋아요"
2. [5/5] "지성피부에 완벽합니다"
...

근거 있는 추천 답변을 제공하세요. 실제 리뷰를 인용하세요.
```

**반환 답변 예시**:
```
# 🎯 3줄 요약
BK001 수분 가득 토너는 지성 피부를 위한 완벽한 선택입니다. 
끈적임 없이 빠르게 흡수되며 뛰어난 보습력을 제공합니다. 
20명의 고객 중 19명이 "끈적임 없다"고 평가했습니다.

## 📊 데이터 기반 분석
- 분석 리뷰: 20개
- 평균 평점: 4.7/5
- 긍정도: 95%

## 🔍 지성 피부 관점 속성별 평가

**✅ 끈적임 (매우 중요)**
점수: 1.2/5 (낮을수록 좋음)
- "끈적임도 없고" (19명 동의)
- "끈기가 전혀 없어서" 아침에 사용하기 좋습니다"

**✅ 보습력**
점수: 4.8/5
- 건조함 없이 촉촉함 유지
- "오후까지 수분감 유지됨"

**✅ 흡수력**
점수: 4.5/5
- 빠른 흡수로 분사 후 즉시 메이크업 가능
- "화장 전 기다릴 필요 없음"

## 💡 최종 판단
**강력히 추천합니다!**

이 제품은 지성 피부의 최대 관심사인 "끈적임 없음"에서 95% 만족도를 기록했습니다.
동시에 충분한 보습력으로 피부 극건조 현상을 막아줍니다.
```

**답변 품질 지표**:
- ✅ 통계 기반 근거
- ✅ 실제 리뷰 인용
- ✅ 사용자 피부타입 반영
- ✅ 명확한 추천/비추천
- ✅ 자연스러운 한국어

---

#### 8️⃣ **Log Query: 쿼리 로그 저장**

**목표**: 사용자 쿼리와 시스템 응답을 기록

**쿼리_logs 테이블**:
```sql
CREATE TABLE query_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    query TEXT NOT NULL,
    answer TEXT,
    reviews_analyzed INTEGER,
    avg_rating DECIMAL(2, 1),
    avg_sentiment DECIMAL(2, 1),
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**저장 데이터**:
```json
{
  "user_id": "user_12345",
  "query": "지성 피부인데 끈적임 없는 토너 추천해줄래?",
  "answer": "BK001 수분 가득 토너는 지성 피부를 위한 완벽한 선택입니다...",
  "reviews_analyzed": 20,
  "avg_rating": 4.7,
  "avg_sentiment": 4.6,
  "response_time_ms": 2840,
  "created_at": "2026-02-06T15:30:00Z"
}
```

**활용**:
- ✅ 사용 분석 및 통계
- ✅ 시스템 성능 모니터링
- ✅ 사용자 선호도 분석
- ✅ 추천 정확도 개선

---

#### 9️⃣ **Respond to Webhook: 사용자에게 응답**

**HTTP 응답**:
```json
{
  "success": true,
  "answer": "BK001 수분 가득 토너는 지성 피부를 위한 완벽한 선택입니다...",
  "metadata": {
    "reviews_analyzed": 20,
    "avg_rating": 4.7,
    "avg_sentiment": 4.6,
    "absa_aspects": 7,
    "generated_at": "2026-02-06T15:30:00Z"
  }
}
```

**HTTP 상태 코드**:
```
200 OK - 정상 응답
400 Bad Request - 입력 검증 실패
500 Internal Server Error - 시스템 오류
```

---

## 데이터 흐름 및 변환

### 🔄 End-to-End 데이터 변환

```
1. RAW 데이터 (Kurly API)
   ├─ product_no: "BK001"
   ├─ name: "수분 가득 토너"
   ├─ reviews: [
   │   {
   │     "id": "REV_123",
   │     "contents": "정말 보습력이 좋아요!",
   │     "rating": 5.0,
   │     "author": {"name": "사용자A"},
   │     "registeredAt": "2026-02-01T10:30:00Z"
   │   }
   │ ]
   └─ ...

2. NORMALIZED 데이터 (Extract Review Data)
   ├─ review_id: "REV_123"
   ├─ product_number: "BK001"
   ├─ content: "정말 보습력이 좋아요!"
   ├─ rating: 5.0
   ├─ created_at: "2026-02-01T10:30:00Z"
   ├─ author: "사용자A"
   └─ ...

3. ENRICHED 데이터 (AI Analysis)
   ├─ (위의 모든 필드)
   ├─ sentiment_score: 5
   ├─ sentiment_label: "Very satisfied"
   ├─ emotions: ["기쁨", "만족감"]
   ├─ key_points: ["보습력 좋음", "흡수 빠름"]
   └─ absa_aspects: {
       "hydration": 5,
       "absorption": 4,
       ...
     }

4. VECTORIZED 데이터 (Embedding)
   ├─ (위의 모든 필드)
   ├─ embedding: [0.123, -0.456, ..., 0.789]  // 1536-dim
   └─ ...

5. STORED 데이터 (PostgreSQL + Qdrant)
   ├─ PostgreSQL: 구조화된 관계형 저장
   │  └─ SELECT/JOIN/GROUP BY 가능
   └─ Qdrant: 벡터 저장
      └─ 의미 유사도 검색 가능
```

### 📊 데이터 크기 추정

```
1개 리뷰:
├─ 텍스트: ~500 bytes
├─ 감정 분석 결과: ~200 bytes
├─ ABSA: ~400 bytes
├─ 임베딩 (1536-dim): ~6 KB
└─ 메타데이터: ~100 bytes
= 약 7.2 KB/리뷰

일일 처리 예시 (10개 제품 × 50개 리뷰):
├─ 총 500개 리뷰
├─ 데이터 크기: 3.6 MB
├─ 벡터 저장소: 3 MB
└─ 메모리 사용: ~50-100 MB
```

---

## 파이프라인 구조

### 🏛️ 병렬 처리 아키텍처

```
┌─────────────────────────────────────────────────┐
│         Main Workflow                           │
│                                                 │
│  Schedule (Daily Midnight)                      │
│         ↓                                       │
│  ┌──────────────────────────────────────────┐  │
│  │ PARALLEL PIPELINE                        │  │
│  │                                          │  │
│  │  Path A: Products        Path B: Reviews │  │
│  │  ├─ Get Products    ├─ Extract Reviews  │  │
│  │  ├─ (10개)         ├─ (병렬 처리)       │  │
│  │  └─ Split Batch    └─ Sentiment Analysis│  │
│  │                       └─ ABSA Analysis   │  │
│  │                       └─ Embedding      │  │
│  │                       └─ Save to DB     │  │
│  │                       └─ Save to Qdrant │  │
│  │                                          │  │
│  └──────────────────────────────────────────┘  │
│         ↓                                       │
│  Webhook Ready for User Queries                │
│                                                 │
└─────────────────────────────────────────────────┘
```

### ⚡ 배치 처리 최적화

```
Products: [10개]
    ↓
Split into Batches
    ├─ Batch 1: [5개] ────┐
    └─ Batch 2: [5개] ────┤
                           ├─ 병렬 처리
    Reviews Fetching ──────┤
    Sentiment Analysis ────┤
    ABSA Analysis ─────────┤
    Embedding ─────────────┤
                           ├─ 동시 완료
    Save to PostgreSQL ────┤
    Save to Qdrant ────────┘
```

**배치 크기 설정**:
```
batchSize: 5

장점:
- ✅ 메모리 효율적
- ✅ API 요청 병렬화
- ✅ 처리 시간 단축

계산:
- 10개 제품 → 2 배치
- 배치당 ~30초 → 총 ~60초 (순차)
- 병렬 처리 → ~30초 (50% 단축)
```

---

## 실무적 고려사항

### 🔐 보안 및 접근 제어

```json
{
  "Credentials Management": {
    "PostgreSQL": {
      "user": "n8n",
      "password": "${POSTGRES_PASSWORD}",
      "encryption": "n8n_encryption_key",
      "scope": "beauty_reviews 테이블 접근만"
    },
    "OpenAI API": {
      "key": "${OPENAI_API_KEY}",
      "rate_limit": "3,500 RPM",
      "usage_tracking": "enabled"
    },
    "Upstage Solar": {
      "key": "${UPSTAGE_API_KEY}",
      "endpoint": "https://api.upstage.ai/v1/solar"
    }
  },
  
  "Data Privacy": {
    "user_id": "익명화 권장",
    "personal_reviews": "GDPR 컴플라이언스",
    "data_retention": "1년"
  }
}
```

### 📈 확장성 고려사항

```
Current State:
├─ 10개 제품/일
├─ ~500개 리뷰/일
└─ ~3.6 MB 데이터/일

Future Scaling (100배):
├─ 1,000개 제품/일
├─ ~50,000개 리뷰/일
└─ ~360 MB 데이터/일

해결책:
1. 배치 크기 조정 (5 → 20)
2. 병렬 워크플로우 추가
3. 데이터베이스 파티셔닝
4. 벡터 DB 클러스터링
```

### 🛡️ 에러 처리 전략

```javascript
// 1. API 타임아웃
try {
  const reviews = await fetchReviews(productId);
} catch (error) {
  if (error.code === 'TIMEOUT') {
    // 재시도 (exponential backoff)
    await retry(async () => fetchReviews(productId), {
      maxAttempts: 3,
      delay: 1000 // 1초
    });
  }
}

// 2. 데이터 유효성
if (!review.content || !review.rating) {
  log.warn(`Invalid review: ${review.id}`);
  continue; // 건너뛰기
}

// 3. AI 분석 실패
if (!sentiment_response || !sentiment_response.sentiment_score) {
  sentiment_score = 3; // 기본값 (중립)
}

// 4. 데이터 중복 확인
const exists = await db.query(
  'SELECT 1 FROM beauty_reviews WHERE review_id = $1',
  [review.review_id]
);
if (exists) {
  // UPDATE 수행
} else {
  // INSERT 수행
}
```

---

## 성능 최적화 전략

### ⚡ 응답 시간 최적화

```
Target Latency: < 5초 (사용자 쿼리 → 최종 답변)

Breakdown:
├─ Query Parsing: 0.5초 (Solar)
├─ Vector Search: 1.0초 (Qdrant)
├─ Keyword Search: 0.5초 (PostgreSQL)
├─ ABSA Aggregation: 0.5초 (Code)
├─ Answer Generation: 2.0초 (Solar)
└─ Response: 0.5초
= 총 5초

최적화:
1. 캐싱: 동일 쿼리는 1시간 캐시
2. 인덱싱: sentiment_score, skin_type 인덱스
3. 배치: 벡터 검색을 20개 요청으로 최적화
4. 비동기: 로그 저장을 백그라운드에서
```

### 💾 저장소 최적화

```sql
-- 1. JSONB 컬럼 인덱싱
CREATE INDEX idx_emotions_gin ON beauty_reviews USING GIN (emotions);
CREATE INDEX idx_absa_gin ON beauty_reviews USING GIN (absa_aspects);

-- 2. 파티셔닝 (대규모 데이터용)
CREATE TABLE beauty_reviews_2026_02 PARTITION OF beauty_reviews
  FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- 3. 아카이빙 (1년 이상 데이터)
SELECT * FROM beauty_reviews WHERE created_at < NOW() - INTERVAL '1 year'
  INTO OUTFILE 'beauty_reviews_archive_2025.sql';
DELETE FROM beauty_reviews WHERE created_at < NOW() - INTERVAL '1 year';
```

---

## 에러 처리 및 안정성

### 🚨 주요 실패 시나리오 및 대응

| 시나리오 | 원인 | 해결책 |
|---------|------|--------|
| **Kurly API 503** | 외부 서비스 다운 | 재시도 3회, 실패 시 로그만 기록 |
| **PostgreSQL 연결 실패** | DB 다운 또는 자격증명 오류 | 헬스체크, 자동 재연결 |
| **OpenAI API Rate Limit** | 요청 초과 | Queue 기반 처리, 요청 대기 |
| **Qdrant 벡터 저장 실패** | 메모리 부족 또는 네트워크 오류 | 로컬 캐시 → 나중에 재시도 |
| **AI 분석 오류** | 모델 오버로드 또는 입력 오류 | 폴백 값 사용 (sentiment_score=3) |
| **사용자 쿼리 파싱 실패** | 모호한 입력 | 기본 필터 적용, 전체 데이터 검색 |

### 📊 모니터링 및 알림

```json
{
  "Metrics": {
    "crawling_duration_seconds": "< 120초",
    "reviews_per_minute": "> 10개",
    "query_latency_ms": "< 5000",
    "error_rate": "< 1%",
    "api_success_rate": "> 99%"
  },
  
  "Alerts": {
    "crawling_timeout": "스케줄링된 크롤링이 30분 이상 지속",
    "high_error_rate": "오류율 > 10%",
    "query_latency_spike": "평균 대비 3배 이상",
    "api_failures": "연속 5회 API 실패"
  },
  
  "Logging": {
    "level": "INFO (프로덕션) / DEBUG (개발)",
    "retention": "30일",
    "format": "JSON (파싱 용이)"
  }
}
```

---

## 결론 및 향후 계획

### ✅ 현재 구현 상태

**완료**:
- ✅ 워크플로우 설계 및 구현
- ✅ PostgreSQL 스키마 정의
- ✅ AI 모델 통합 (Sentiment, ABSA)
- ✅ 벡터 임베딩 파이프라인
- ✅ 쿼리 응답 시스템

**진행 중**:
- 🔄 n8n 워크플로우 활성화
- 🔄 실제 데이터 테스트
- 🔄 성능 튜닝

### 📋 향후 개선 로드맵

**Phase 2 (2-4주)**:
```
- 사용자 피드백 수집
- 모니터링 대시보드 구축
- API 응답 성능 최적화
- 비용 분석 (API 사용료)
```

**Phase 3 (1-2개월)**:
```
- 추천 알고리즘 고도화
- 사용자별 맞춤 학습 (ML)
- 모바일 앱 API 제공
- 한국 이커머스 플랫폼 확대 (G마켓, 쿠팡 등)
```

**Phase 4 (3-6개월)**:
```
- 다국어 지원
- 실시간 재고 연동
- 채팅봇 인터페이스
- 영상 기반 제품 분석
```

---

## 부록: 기술 스택 상세 정보

### 🔗 API 엔드포인트

```
n8n Webhooks:
├─ POST /webhook/beauty-kurly-agent → 크롤링 트리거
└─ POST /webhook/beauty-query → 사용자 쿼리

External APIs:
├─ https://api.kurly.com/v2/reviews/products/{id} → 리뷰 크롤링
├─ https://api.openai.com/v1/embeddings → 벡터 생성
├─ https://api.openai.com/v1/chat/completions → 답변 생성
└─ https://api.upstage.ai/v1/solar → 감정분석

Database:
├─ postgresql://n8n:password@postgres:5432/n8n
└─ Qdrant at http://qdrant:6333

Monitoring:
└─ n8n Execution Logs at http://localhost:5678
```

### 📚 참고 자료

```
[1] n8n Documentation: https://docs.n8n.io
[2] PostgreSQL JSONB: https://www.postgresql.org/docs/14/datatype-json.html
[3] Qdrant Vector Search: https://qdrant.tech/documentation
[4] OpenAI API: https://platform.openai.com/docs
[5] Upstage Solar: https://console.upstage.ai/docs
```

---

**문서 버전**: 1.0  
**마지막 업데이트**: 2026-02-06  
**작성자**: AI Copilot  
**상태**: 진행 중
