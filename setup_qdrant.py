#!/usr/bin/env python3
"""
Qdrant Vector Database Setup Script
뷰티컬리 쇼핑 에이전트를 위한 Qdrant 컬렉션 초기화
"""

import requests
import json
import time

# Qdrant 설정
QDRANT_HOST = "http://localhost:6333"
COLLECTION_NAME = "beauty_reviews"

# OpenAI text-embedding-3-small 모델의 벡터 차원
VECTOR_SIZE = 1536


def check_qdrant_health():
    """Qdrant 서버 상태 확인"""
    try:
        response = requests.get(f"{QDRANT_HOST}/")
        if response.status_code == 200:
            print("✅ Qdrant 서버가 정상적으로 실행 중입니다.")
            return True
        else:
            print(f"❌ Qdrant 서버 상태 이상: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Qdrant 서버에 연결할 수 없습니다. Docker 컨테이너가 실행 중인지 확인하세요.")
        return False


def delete_collection_if_exists():
    """기존 컬렉션 삭제 (재설정 시)"""
    try:
        response = requests.delete(f"{QDRANT_HOST}/collections/{COLLECTION_NAME}")
        if response.status_code == 200:
            print(f"✅ 기존 컬렉션 '{COLLECTION_NAME}' 삭제 완료")
        elif response.status_code == 404:
            print(f"ℹ️  컬렉션 '{COLLECTION_NAME}'이 존재하지 않습니다.")
        else:
            print(f"⚠️  컬렉션 삭제 실패: {response.text}")
    except Exception as e:
        print(f"❌ 컬렉션 삭제 중 오류: {e}")


def create_collection():
    """Qdrant 컬렉션 생성"""
    collection_config = {
        "vectors": {
            "size": VECTOR_SIZE,
            "distance": "Cosine"  # 코사인 유사도 사용
        },
        "optimizers_config": {
            "default_segment_number": 2
        },
        "replication_factor": 1
    }
    
    try:
        response = requests.put(
            f"{QDRANT_HOST}/collections/{COLLECTION_NAME}",
            json=collection_config,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ 컬렉션 '{COLLECTION_NAME}' 생성 완료")
            print(f"   - 벡터 차원: {VECTOR_SIZE}")
            print(f"   - 거리 측정: Cosine Similarity")
            return True
        else:
            print(f"❌ 컬렉션 생성 실패: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 컬렉션 생성 중 오류: {e}")
        return False


def create_payload_indexes():
    """페이로드 필드에 인덱스 생성 (검색 성능 향상)"""
    indexes = [
        {
            "field_name": "product_number",
            "field_schema": "keyword"
        },
        {
            "field_name": "sentiment_score",
            "field_schema": "integer"
        },
        {
            "field_name": "sentiment_label",
            "field_schema": "keyword"
        },
        {
            "field_name": "rating",
            "field_schema": "float"
        }
    ]
    
    for index in indexes:
        try:
            response = requests.put(
                f"{QDRANT_HOST}/collections/{COLLECTION_NAME}/index",
                json=index,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ 인덱스 생성 완료: {index['field_name']}")
            else:
                print(f"⚠️  인덱스 생성 실패: {index['field_name']} - {response.text}")
        except Exception as e:
            print(f"❌ 인덱스 생성 중 오류: {e}")


def get_collection_info():
    """컬렉션 정보 조회"""
    try:
        response = requests.get(f"{QDRANT_HOST}/collections/{COLLECTION_NAME}")
        
        if response.status_code == 200:
            info = response.json()
            result = info.get("result", {})
            
            print("\n📊 컬렉션 정보:")
            print(f"   - 이름: {result.get('name')}")
            print(f"   - 포인트 수: {result.get('points_count', 0)}")
            print(f"   - 벡터 차원: {result.get('config', {}).get('params', {}).get('vectors', {}).get('size')}")
            print(f"   - 거리 측정: {result.get('config', {}).get('params', {}).get('vectors', {}).get('distance')}")
            print(f"   - 상태: {result.get('status')}")
        else:
            print(f"❌ 컬렉션 정보 조회 실패: {response.text}")
    except Exception as e:
        print(f"❌ 컬렉션 정보 조회 중 오류: {e}")


def insert_sample_data():
    """샘플 데이터 삽입 (테스트용)"""
    # 실제로는 n8n 워크플로우에서 임베딩을 생성하여 삽입
    # 여기서는 0으로 채운 더미 벡터 사용
    sample_points = {
        "points": [
            {
                "id": 1,
                "vector": [0.0] * VECTOR_SIZE,
                "payload": {
                    "review_id": "SAMPLE001",
                    "product_number": "BK001",
                    "content": "정말 보습력이 좋아요!",
                    "rating": 5.0,
                    "sentiment_score": 5,
                    "sentiment_label": "긍정",
                    "created_at": "2026-02-04T00:00:00Z"
                }
            }
        ]
    }
    
    try:
        response = requests.put(
            f"{QDRANT_HOST}/collections/{COLLECTION_NAME}/points",
            json=sample_points,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201]:
            print("✅ 샘플 데이터 삽입 완료")
        else:
            print(f"⚠️  샘플 데이터 삽입 실패: {response.text}")
    except Exception as e:
        print(f"❌ 샘플 데이터 삽입 중 오류: {e}")


def main():
    print("=" * 60)
    print("Qdrant Vector Database 초기화")
    print("뷰티컬리 쇼핑 에이전트 워크플로우")
    print("=" * 60)
    print()
    
    # 1. Qdrant 서버 상태 확인
    if not check_qdrant_health():
        print("\n❌ Qdrant 서버를 먼저 시작하세요:")
        print("   docker-compose up -d qdrant")
        return
    
    print()
    
    # 2. 기존 컬렉션 삭제 (선택사항)
    user_input = input(f"기존 컬렉션 '{COLLECTION_NAME}'을 삭제하시겠습니까? (y/N): ")
    if user_input.lower() == 'y':
        delete_collection_if_exists()
        time.sleep(1)
    
    print()
    
    # 3. 컬렉션 생성
    if not create_collection():
        return
    
    time.sleep(1)
    print()
    
    # 4. 인덱스 생성
    print("📑 페이로드 인덱스 생성 중...")
    create_payload_indexes()
    
    time.sleep(1)
    print()
    
    # 5. 샘플 데이터 삽입 (선택사항)
    user_input = input("샘플 데이터를 삽입하시겠습니까? (y/N): ")
    if user_input.lower() == 'y':
        insert_sample_data()
        time.sleep(1)
    
    print()
    
    # 6. 컬렉션 정보 확인
    get_collection_info()
    
    print()
    print("=" * 60)
    print("✅ Qdrant 초기화 완료!")
    print("=" * 60)
    print()
    print("다음 단계:")
    print("1. n8n 워크플로우를 임포트하세요")
    print("2. PostgreSQL 스키마를 적용하세요 (database_schema.sql)")
    print("3. OpenAI API 키를 n8n 크리덴셜에 등록하세요")
    print("4. 워크플로우를 활성화하고 테스트하세요")


if __name__ == "__main__":
    main()
