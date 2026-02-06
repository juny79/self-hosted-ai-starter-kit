#!/usr/bin/env python3
"""
뷰티컬리 쇼핑 에이전트 API 테스트 스크립트
n8n 워크플로우 webhook 엔드포인트 테스트
"""

import requests
import json
import time
from datetime import datetime


# 설정
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/beauty-query"
N8N_WEBHOOK_TEST_URL = "http://localhost:5678/webhook-test/beauty-query"

# 자동으로 올바른 URL 찾기
def find_active_webhook_url():
    """활성화된 webhook URL 찾기"""
    urls_to_try = [
        N8N_WEBHOOK_URL,
        N8N_WEBHOOK_TEST_URL,
        "http://localhost:5678/webhook/beauty-kurly-agent",
        "http://localhost:5678/webhook-test/beauty-kurly-agent"
    ]
    
    for url in urls_to_try:
        try:
            response = requests.post(
                url,
                json={"query": "테스트", "user_id": "health_check"},
                timeout=5
            )
            # 200, 201, 204 모두 성공으로 간주
            if response.status_code in [200, 201, 204, 400, 500]:
                return url
        except:
            continue
    
    return N8N_WEBHOOK_URL  # 기본값

# 실제 사용할 URL
ACTIVE_WEBHOOK_URL = find_active_webhook_url()


# 테스트 쿼리 샘플
TEST_QUERIES = [
    {
        "query": "건조한 피부에 좋은 토너 추천해줘",
        "user_id": "test_user_001",
        "description": "건성 피부 토너 추천"
    },
    {
        "query": "지성 피부에 끈적이지 않는 에센스 찾아줘",
        "user_id": "test_user_002",
        "description": "지성 피부 에센스"
    },
    {
        "query": "민감성 피부를 진정시키는 크림 비교해줘",
        "user_id": "test_user_003",
        "description": "민감성 피부 크림 비교"
    },
    {
        "query": "비타민 세럼 리뷰 요약해줘",
        "user_id": "test_user_004",
        "description": "비타민 세럼 리뷰 요약"
    },
    {
        "query": "3만원대 가성비 좋은 보습 제품 추천",
        "user_id": "test_user_005",
        "description": "가성비 보습 제품"
    }
]


def print_header():
    """헤더 출력"""
    print("=" * 70)
    print("뷰티컬리 쇼핑 에이전트 API 테스트")
    print("=" * 70)
    print()


def test_webhook_availability():
    """Webhook 엔드포인트 가용성 확인"""
    print("🔍 Webhook 엔드포인트 확인 중...")
    print(f"   URL: {ACTIVE_WEBHOOK_URL}")
    
    try:
        response = requests.post(
            ACTIVE_WEBHOOK_URL,
            json={"query": "test", "user_id": "health_check"},
            timeout=10
        )
        
        print(f"   응답 코드: {response.status_code}")
        
        # 204는 워크플로우가 실행되었지만 응답이 없음을 의미
        if response.status_code == 204:
            print("   ⚠️  워크플로우가 실행되었지만 응답이 없습니다")
            print("   💡 워크플로우 확인이 필요합니다:")
            print("      1. n8n UI에서 워크플로우 열기")
            print("      2. 'Respond to Webhook' 노드가 제대로 연결되어 있는지 확인")
            print("      3. 워크플로우 재저장 및 재활성화")
            return True  # 워크플로우는 실행되므로 True
        elif response.status_code in [200, 201]:
            print("   ✅ Webhook 엔드포인트 정상 작동")
            return True
        elif response.status_code == 404:
            print("   ❌ Webhook을 찾을 수 없습니다 (404)")
            print("   💡 해결 방법:")
            print("      1. n8n UI 접속: http://localhost:5678")
            print("      2. 워크플로우 임포트 및 활성화")
            return False
        elif response.status_code >= 500:
            print(f"   ⚠️  서버 오류 ({response.status_code})")
            print(f"   응답: {response.text[:200]}")
            return True  # 워크플로우는 존재하지만 실행 중 오류
        else:
            print(f"   ⚠️  예상치 못한 응답 코드: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ n8n 서버에 연결할 수 없습니다!")
        print("   💡 docker-compose up -d 명령으로 서비스를 시작하세요.")
        return False
    except requests.exceptions.Timeout:
        print("   경고: 요청 시간 초과 (10초)")
        print("   워크플로우가 너무 오래 걸리거나 응답하지 않습니다")
        return False
    except Exception as e:
        print(f"   오류 발생: {e}")
        return False


def send_query(query_data, index=None, total=None):
    """쿼리 전송 및 응답 확인"""
    header = f"[{index}/{total}]" if index and total else ""
    
    print()
    print(f"{header} 테스트: {query_data['description']}")
    print("-" * 70)
    print(f"📝 쿼리: {query_data['query']}")
    print(f"👤 사용자 ID: {query_data['user_id']}")
    
    # 요청 시작 시간
    start_time = time.time()
    
    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json={
                "query": query_data["query"],
                "user_id": query_data["user_id"]
            },
            headers={"Content-Type": "application/json"},
            timeout=60  # 60초 타임아웃
        )
        
        # 응답 시간 계산
        elapsed_time = time.time() - start_time
        
        # 응답 상태 확인
        if response.status_code == 204:
            print(f"⚠️  응답 없음 (204 No Content)")
            print("워크플로우가 실행되었지만 응답을 반환하지 않았습니다.")
            print("n8n UI에서 워크플로우의 'Respond to Webhook' 노드를 확인하세요.")
            return {"success": False, "error": "No response (204)"}
        elif response.status_code == 200:
            print(f"✅ 응답 성공 (소요 시간: {elapsed_time:.2f}초)")
            
            # JSON 파싱
            try:
                result = response.json()
                
                # 메타데이터 출력
                if "metadata" in result:
                    metadata = result["metadata"]
                    print()
                    print("📊 메타데이터:")
                    print(f"   - 분석된 리뷰: {metadata.get('reviews_analyzed', 'N/A')}개")
                    print(f"   - 평균 평점: {metadata.get('avg_rating', 'N/A')}/5")
                    print(f"   - 평균 감정 점수: {metadata.get('avg_sentiment', 'N/A')}/5")
                    print(f"   - ABSA 속성 수: {metadata.get('absa_aspects', 'N/A')}개")
                    print(f"   - 생성 시간: {metadata.get('generated_at', 'N/A')}")
                
                # 답변 출력 (처음 500자만)
                if "answer" in result:
                    answer = result["answer"]
                    print()
                    print("💡 답변 (처음 500자):")
                    print("-" * 70)
                    print(answer[:500])
                    if len(answer) > 500:
                        print("... (생략) ...")
                    print("-" * 70)
                
                return {
                    "success": True,
                    "elapsed_time": elapsed_time,
                    "metadata": result.get("metadata", {})
                }
                
            except json.JSONDecodeError:
                print("⚠️  JSON 파싱 실패")
                print(f"응답 내용: {response.text[:200]}")
                return {"success": False, "error": "JSON 파싱 실패"}
        else:
            print(f"❌ 응답 실패 (HTTP {response.status_code})")
            print(f"오류 내용: {response.text[:200]}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.Timeout:
        print("❌ 타임아웃 (60초 초과)")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return {"success": False, "error": str(e)}


def run_all_tests():
    """모든 테스트 실행"""
    print_header()
    
    # Webhook 가용성 확인
    if not test_webhook_availability():
        print()
        print("❌ 테스트를 계속할 수 없습니다.")
        return
    
    print()
    print(f"🧪 총 {len(TEST_QUERIES)}개 테스트 실행")
    print()
    
    # 결과 저장
    results = []
    
    # 각 쿼리 테스트
    for idx, query_data in enumerate(TEST_QUERIES, 1):
        result = send_query(query_data, idx, len(TEST_QUERIES))
        results.append(result)
        
        # 마지막 테스트가 아니면 대기
        if idx < len(TEST_QUERIES):
            print()
            print("⏳ 다음 테스트까지 3초 대기...")
            time.sleep(3)
    
    # 결과 요약
    print()
    print("=" * 70)
    print("📈 테스트 결과 요약")
    print("=" * 70)
    
    success_count = sum(1 for r in results if r.get("success"))
    fail_count = len(results) - success_count
    
    print(f"✅ 성공: {success_count}/{len(results)}")
    print(f"❌ 실패: {fail_count}/{len(results)}")
    
    if success_count > 0:
        avg_time = sum(r.get("elapsed_time", 0) for r in results if r.get("success")) / success_count
        print(f"⏱️  평균 응답 시간: {avg_time:.2f}초")
    
    # 실패한 테스트 상세
    if fail_count > 0:
        print()
        print("❌ 실패한 테스트:")
        for idx, (query, result) in enumerate(zip(TEST_QUERIES, results), 1):
            if not result.get("success"):
                print(f"   [{idx}] {query['description']}: {result.get('error', 'Unknown error')}")
    
    print()
    print("=" * 70)


def run_single_test():
    """단일 테스트 실행 (대화형)"""
    print_header()
    
    print("🔍 단일 쿼리 테스트")
    print()
    
    query = input("질문을 입력하세요: ")
    user_id = input("사용자 ID (Enter: 기본값): ") or f"test_user_{int(time.time())}"
    
    query_data = {
        "query": query,
        "user_id": user_id,
        "description": "사용자 입력"
    }
    
    result = send_query(query_data)
    
    if result.get("success"):
        print()
        print("✅ 테스트 완료!")
    else:
        print()
        print("❌ 테스트 실패")


def main():
    """메인 함수"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        run_single_test()
    else:
        run_all_tests()


if __name__ == "__main__":
    main()
