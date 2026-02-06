# 뷰티컬리 쇼핑 에이전트 워크플로우 - 생성 완료

## 📦 생성된 파일 목록

### 1. n8n 워크플로우
- **파일**: `n8n/demo-data/workflows/workflow-beauty-kurly-shopping-agent.json`
- **설명**: 완전한 n8n 워크플로우 정의 (28개 노드)
- **기능**:
  - 자동 리뷰 크롤링 (매일 자정)
  - AI 감정 분석 + ABSA
  - 벡터 임베딩 생성
  - 하이브리드 검색 (벡터 + 키워드)
  - 전문가급 답변 생성

### 2. 데이터베이스 스키마
- **파일**: `database_schema.sql`
- **설명**: PostgreSQL 데이터베이스 스키마
- **포함 내용**:
  - 제품 테이블 (products)
  - 리뷰 테이블 (beauty_reviews)
  - 쿼리 로그 테이블 (query_logs)
  - 통계 뷰
  - 인덱스 및 트리거
  - 샘플 데이터

### 3. Qdrant 설정 스크립트
- **파일**: `setup_qdrant.py`
- **설명**: Qdrant Vector Database 초기화 Python 스크립트
- **기능**:
  - 서버 상태 확인
  - 컬렉션 생성 (1536차원)
  - 페이로드 인덱스 생성
  - 샘플 데이터 삽입

### 4. 완전한 가이드
- **파일**: `BEAUTY_KURLY_WORKFLOW_GUIDE.md`
- **설명**: 포괄적인 설치 및 사용 가이드
- **포함 내용**:
  - 시스템 아키텍처
  - 설치 단계별 가이드
  - API 사용 방법
  - 트러블슈팅
  - 성능 최적화

### 5. 자동 설정 스크립트
- **파일**: `setup-beauty-kurly-workflow.ps1`
- **설명**: Windows PowerShell 자동 설정 스크립트
- **기능**:
  - Docker 컨테이너 시작
  - PostgreSQL 스키마 자동 적용
  - Qdrant 자동 초기화
  - 서비스 상태 확인
  - n8n 브라우저 자동 실행

### 6. API 테스트 스크립트
- **파일**: `test_beauty_agent.py`
- **설명**: Python API 테스트 스크립트
- **기능**:
  - 5개 테스트 케이스 자동 실행
  - 응답 시간 측정
  - 결과 분석 및 요약
  - 단일 쿼리 대화형 테스트

## 🚀 빠른 시작 가이드

### Windows 사용자

1. **PowerShell에서 실행**:
   ```powershell
   .\setup-beauty-kurly-workflow.ps1
   ```

2. **n8n 접속**: http://localhost:5678

3. **워크플로우 임포트**:
   - Workflows → Import from File
   - 파일 선택: `n8n/demo-data/workflows/workflow-beauty-kurly-shopping-agent.json`

4. **Credentials 설정**:
   - OpenAI API Key
   - PostgreSQL (자동 설정됨)

5. **활성화 및 테스트**:
   ```bash
   python test_beauty_agent.py
   ```

### Linux/Mac 사용자

1. **Docker 시작**:
   ```bash
   docker-compose up -d
   ```

2. **PostgreSQL 스키마 적용**:
   ```bash
   docker-compose exec -T postgres psql -U n8n -d n8n < database_schema.sql
   ```

3. **Qdrant 초기화**:
   ```bash
   python setup_qdrant.py
   ```

4. **n8n 접속 및 워크플로우 임포트** (위와 동일)

## 📊 워크플로우 구조 요약

### 파이프라인 1: 자동 크롤링
```
Schedule (자정) → Get Products → Fetch Reviews
→ Sentiment Analysis → ABSA → Embedding
→ Save PostgreSQL → Save Qdrant → Slack 알림
```

### 파이프라인 2: 사용자 쿼리
```
Webhook → Parse Intent → Embedding
→ Vector Search (Qdrant) + Keyword Search (PostgreSQL)
→ Merge Results → ABSA Aggregation
→ Generate Answer (GPT-4o) → Response
```

## 🎯 주요 기능

### 1. AI 감정 분석
- **모델**: GPT-4o-mini
- **점수**: 1-5점 척도
- **라벨**: 긍정/중립/부정
- **추가**: 감정 키워드, 핵심 포인트

### 2. ABSA (Aspect-Based Sentiment Analysis)
분석 속성:
- 보습력 (hydration)
- 흡수력 (absorption)
- 끈적임 (stickiness)
- 향 (fragrance)
- 자극성 (irritation)
- 가성비 (value)
- 효과 (effectiveness)

### 3. 하이브리드 검색
- **벡터 검색** (60%): Qdrant Cosine Similarity
- **키워드 검색** (40%): PostgreSQL ILIKE
- **병합**: 가중치 기반 점수 통합

### 4. 전문가급 답변
- **모델**: GPT-4o
- **역할**: 10년 경력 뷰티 MD
- **구조**: 3줄 요약 + 데이터 분석 + 속성별 평가 + 장단점 + 최종 판단

## 🔧 기술 스택

- **워크플로우 엔진**: n8n
- **AI/ML**: OpenAI (GPT-4o, GPT-4o-mini, text-embedding-3-small)
- **벡터 DB**: Qdrant (Cosine Similarity)
- **관계형 DB**: PostgreSQL 14+
- **컨테이너**: Docker & Docker Compose
- **알림**: Slack (선택사항)

## 📈 성능 지표

- **크롤링 주기**: 매일 자정
- **배치 크기**: 제품 5개씩
- **벡터 차원**: 1536 (OpenAI embedding-3-small)
- **검색 threshold**: 0.7 (코사인 유사도)
- **검색 결과**: 최대 20개 (각 파이프라인)
- **최종 결과**: Top 15개 병합

## 🔒 보안 고려사항

1. **환경 변수**: API 키는 .env에 저장
2. **Basic Auth**: n8n 접근 제한
3. **PostgreSQL**: 강력한 비밀번호 설정
4. **네트워크**: Docker 내부 네트워크 사용
5. **Webhook**: HTTPS 사용 권장 (프로덕션)

## 📝 API 엔드포인트

### POST /webhook/beauty-query

**요청**:
```json
{
  "query": "건조한 피부에 좋은 토너 추천해줘",
  "user_id": "user123"
}
```

**응답**:
```json
{
  "success": true,
  "answer": "# 🎯 3줄 요약\n...",
  "metadata": {
    "reviews_analyzed": 15,
    "avg_rating": 4.3,
    "avg_sentiment": 4.2,
    "absa_aspects": 7,
    "generated_at": "2026-02-04T10:30:00.000Z"
  }
}
```

## 🧪 테스트

### 자동 테스트 (5개 케이스)
```bash
python test_beauty_agent.py
```

### 단일 쿼리 테스트
```bash
python test_beauty_agent.py --single
```

### cURL 테스트
```bash
curl -X POST http://localhost:5678/webhook/beauty-query \
  -H "Content-Type: application/json" \
  -d '{"query": "지성 피부 에센스 추천", "user_id": "test"}'
```

## 📚 추가 리소스

- [완전한 가이드](BEAUTY_KURLY_WORKFLOW_GUIDE.md)
- [n8n Documentation](https://docs.n8n.io/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

## 🐛 트러블슈팅

### 일반적인 문제

1. **Docker 연결 오류**
   ```bash
   docker-compose restart
   ```

2. **PostgreSQL 권한 오류**
   ```sql
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO n8n;
   ```

3. **Qdrant 차원 불일치**
   ```bash
   python setup_qdrant.py  # 재생성
   ```

4. **OpenAI Rate Limit**
   - API 키 확인
   - 배치 크기 조정

## 📞 지원

문제가 발생하면:
1. [BEAUTY_KURLY_WORKFLOW_GUIDE.md](BEAUTY_KURLY_WORKFLOW_GUIDE.md) 참조
2. Docker 로그 확인: `docker-compose logs -f n8n`
3. GitHub Issues 등록

## 🎉 완료!

뷰티컬리 쇼핑 에이전트 워크플로우가 성공적으로 생성되었습니다!

다음 단계:
1. ✅ PowerShell 스크립트 실행
2. ✅ n8n에서 워크플로우 임포트
3. ✅ OpenAI API 키 설정
4. ✅ 워크플로우 활성화
5. ✅ 테스트 실행

Happy Automating! 🚀
