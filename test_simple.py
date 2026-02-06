#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
뷰티컬리 쇼핑 에이전트 API 테스트 스크립트 (간소화 버전)
"""

import requests
import json
import time

# 설정
WEBHOOK_URLS = [
    "http://localhost:5678/webhook/beauty-query",
    "http://localhost:5678/webhook-test/beauty-query",
]

# 테스트 쿼리
TEST_QUERY = {
    "query": "건조한 피부에 좋은 토너 추천해줘",
    "user_id": "test_user_001"
}

def find_active_url():
    """활성 Webhook URL 찾기"""
    for url in WEBHOOK_URLS:
        try:
            response = requests.post(url, json=TEST_QUERY, timeout=5)
            if response.status_code in [200, 201, 204, 400, 500]:
                return url, response.status_code
        except:
            continue
    return None, None

print("=" * 70)
print("뷰티컬리 쇼핑 에이전트 API 테스트")
print("=" * 70)
print()

# 1. 활성 URL 찾기
print("[1/2] Webhook URL 탐지 중...")
active_url, status_code = find_active_url()

if not active_url:
    print("오류: 활성 Webhook을 찾을 수 없습니다!")
    print()
    print("해결 방법:")
    print("1. n8n 접속: http://localhost:5678")
    print("2. 워크플로우 임포트: workflow-beauty-kurly-shopping-agent.json")
    print("3. 워크플로우 활성화 (Active 스위치 ON)")
    print("4. 다시 테스트 실행")
    exit(1)

print(f"발견된 URL: {active_url}")
print(f"초기 응답 코드: {status_code}")
print()

# 2. 실제 테스트
print("[2/2] API 테스트 실행 중...")
print(f"질문: {TEST_QUERY['query']}")
print()

start_time = time.time()

try:
    response = requests.post(
        active_url,
        json=TEST_QUERY,
        headers={"Content-Type": "application/json"},
        timeout=60
    )
    
    elapsed = time.time() - start_time
    
    print(f"응답 코드: {response.status_code}")
    print(f"소요 시간: {elapsed:.2f}초")
    print()
    
    if response.status_code == 204:
        print("경고: 워크플로우가 실행되었지만 응답이 없습니다 (204)")
        print()
        print("확인 사항:")
        print("1. n8n UI에서 워크플로우 실행 로그 확인")
        print("2. 'Respond to Webhook' 노드가 올바르게 연결되었는지 확인")
        print("3. 워크플로우에 오류가 없는지 확인")
        print()
        print("가능한 원인:")
        print("- PostgreSQL 연결 오류")
        print("- OpenAI API 키 미설정")
        print("- 데이터베이스 테이블 미생성")
        
    elif response.status_code == 200:
        print("성공! 응답 받음")
        print()
        
        try:
            result = response.json()
            
            if "metadata" in result:
                meta = result["metadata"]
                print("메타데이터:")
                print(f"  - 분석된 리뷰: {meta.get('reviews_analyzed', 'N/A')}개")
                print(f"  - 평균 평점: {meta.get('avg_rating', 'N/A')}/5")
                print(f"  - 평균 감정: {meta.get('avg_sentiment', 'N/A')}/5")
                print()
            
            if "answer" in result:
                answer = result["answer"]
                print("답변 (처음 300자):")
                print("-" * 70)
                print(answer[:300])
                if len(answer) > 300:
                    print("...")
                print("-" * 70)
            else:
                print("응답에 'answer' 필드가 없습니다")
                print(f"응답 내용: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
                
        except json.JSONDecodeError:
            print("JSON 파싱 실패")
            print(f"응답 내용: {response.text[:300]}")
    
    elif response.status_code >= 500:
        print(f"서버 오류 ({response.status_code})")
        print(f"오류 메시지: {response.text[:500]}")
        print()
        print("n8n 워크플로우 실행 중 오류가 발생했습니다.")
        print("n8n UI에서 워크플로우 실행 로그를 확인하세요.")
        
    elif response.status_code == 404:
        print("404 Not Found - Webhook을 찾을 수 없습니다")
        print("워크플로우가 비활성화되었거나 삭제되었습니다.")
        
    else:
        print(f"예상치 못한 응답 코드: {response.status_code}")
        print(f"응답: {response.text[:300]}")
        
except requests.exceptions.Timeout:
    print("타임아웃 (60초 초과)")
    print("워크플로우 실행이 너무 오래 걸립니다.")
    
except requests.exceptions.ConnectionError:
    print("연결 오류: n8n 서버에 연결할 수 없습니다")
    print("docker-compose ps 명령으로 n8n이 실행 중인지 확인하세요")
    
except Exception as e:
    print(f"오류 발생: {e}")

print()
print("=" * 70)
print("테스트 완료")
print("=" * 70)
