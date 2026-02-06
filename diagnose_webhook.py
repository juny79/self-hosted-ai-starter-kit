#!/usr/bin/env python3
"""
n8n Webhook 진단 스크립트
404 오류 원인 파악
"""

import requests
import json

print("=" * 70)
print("n8n Webhook 진단 도구")
print("=" * 70)
print()

# 1. n8n 서버 상태 확인
print("1️⃣  n8n 서버 상태 확인...")
try:
    response = requests.get("http://localhost:5678/healthz", timeout=5)
    if response.status_code == 200:
        print("   ✅ n8n 서버 실행 중")
    else:
        print(f"   ⚠️  예상치 못한 응답: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("   ❌ n8n 서버에 연결할 수 없습니다!")
    print("   💡 해결 방법: docker-compose up -d")
    exit(1)
except Exception as e:
    print(f"   ❌ 오류: {e}")
    exit(1)

print()

# 2. 다양한 webhook 경로 테스트
print("2️⃣  Webhook 경로 테스트...")
print()

test_paths = [
    "/webhook/beauty-query",
    "/webhook-test/beauty-query",
    "/webhook/beauty-kurly-agent",
    "/webhook-test/beauty-kurly-agent",
]

found_path = None

for path in test_paths:
    url = f"http://localhost:5678{path}"
    try:
        # OPTIONS 요청으로 경로 확인
        response = requests.options(url, timeout=2)
        status = response.status_code
        
        # POST로도 시도
        if status == 404:
            response = requests.post(
                url,
                json={"query": "test", "user_id": "diagnostic"},
                timeout=2
            )
            status = response.status_code
        
        if status != 404:
            print(f"   ✅ {path} - 응답 코드: {status}")
            found_path = path
            break
        else:
            print(f"   ❌ {path} - 404 Not Found")
    except Exception as e:
        print(f"   ❌ {path} - 오류: {str(e)[:50]}")

print()

if not found_path:
    print("=" * 70)
    print("❌ 활성화된 Webhook을 찾을 수 없습니다!")
    print("=" * 70)
    print()
    print("📋 체크리스트:")
    print()
    print("1. n8n 웹 인터페이스 접속")
    print("   👉 http://localhost:5678")
    print()
    print("2. 워크플로우 확인")
    print("   - Workflows 메뉴에서 'Beauty Kurly Shopping Agent' 워크플로우가 있는지 확인")
    print("   - 없다면: Import from File → workflow-beauty-kurly-shopping-agent.json")
    print()
    print("3. 워크플로우 활성화")
    print("   - 워크플로우 열기")
    print("   - 우측 상단 'Active' 스위치를 ON으로 변경")
    print("   - 'Save' 버튼 클릭")
    print()
    print("4. Webhook URL 확인")
    print("   - 'User Query Webhook' 노드 클릭")
    print("   - 'Webhook URLs' 섹션에서 Production URL 확인")
    print("   - 예상 URL: http://localhost:5678/webhook/beauty-query")
    print()
    print("5. Credentials 설정")
    print("   - Settings → Credentials")
    print("   - PostgreSQL 연결 정보 입력")
    print("   - OpenAI API 키 입력")
    print()
    print("💡 빠른 가이드:")
    print("   BEAUTY_KURLY_WORKFLOW_GUIDE.md 파일 참조")
    print()
else:
    print("=" * 70)
    print("✅ Webhook 발견!")
    print("=" * 70)
    print()
    print(f"활성 경로: http://localhost:5678{found_path}")
    print()
    print("테스트 명령어:")
    print(f"  python test_beauty_agent.py")
    print()

# 3. n8n API로 워크플로우 목록 조회 시도 (인증 없이)
print()
print("3️⃣  추가 정보...")
print()

try:
    # n8n의 webhook-test 엔드포인트 확인
    response = requests.get("http://localhost:5678/", timeout=2)
    if "n8n" in response.text.lower():
        print("   ℹ️  n8n 프론트엔드 접근 가능")
        print("   👉 브라우저에서 http://localhost:5678 접속하여 확인하세요")
except:
    pass

print()
print("=" * 70)
print()
print("🔧 문제 해결 단계:")
print()
print("Step 1: n8n 웹 UI 접속")
print("  브라우저: http://localhost:5678")
print()
print("Step 2: 로그인")
print("  기본 인증 정보는 .env 파일 확인")
print()
print("Step 3: 워크플로우 임포트 & 활성화")
print("  Workflows → Import → workflow-beauty-kurly-shopping-agent.json")
print()
print("Step 4: Webhook URL 복사")
print("  User Query Webhook 노드 → Production URL")
print()
print("Step 5: test_beauty_agent.py 수정")
print("  N8N_WEBHOOK_URL을 실제 URL로 변경")
print()
