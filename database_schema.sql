-- Beauty Kurly Shopping Agent Database Schema
-- PostgreSQL 데이터베이스 스키마 정의

-- 제품 테이블
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_number VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    price DECIMAL(10, 2),
    original_price DECIMAL(10, 2),
    discount_rate DECIMAL(5, 2),
    description TEXT,
    ingredients TEXT,
    image_url VARCHAR(500),
    product_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 리뷰 테이블
CREATE TABLE IF NOT EXISTS beauty_reviews (
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
    
    -- ABSA (Aspect-Based Sentiment Analysis)
    absa_aspects JSONB,
    
    -- 임베딩은 Qdrant에 저장
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (product_number) REFERENCES products(product_number) ON DELETE CASCADE
);

-- 쿼리 로그 테이블
CREATE TABLE IF NOT EXISTS query_logs (
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

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_reviews_product ON beauty_reviews(product_number);
CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON beauty_reviews(sentiment_score);
CREATE INDEX IF NOT EXISTS idx_reviews_created ON beauty_reviews(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON beauty_reviews(rating DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_skin_type ON beauty_reviews(skin_type);
CREATE INDEX IF NOT EXISTS idx_query_logs_user ON query_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_created ON query_logs(created_at DESC);

-- ABSA 속성별 집계를 위한 GIN 인덱스
CREATE INDEX IF NOT EXISTS idx_reviews_absa_gin ON beauty_reviews USING GIN (absa_aspects);
CREATE INDEX IF NOT EXISTS idx_reviews_emotions_gin ON beauty_reviews USING GIN (emotions);

-- 샘플 제품 데이터 삽입
INSERT INTO products (product_number, name, brand, category, subcategory, price, original_price, discount_rate, description) VALUES
('BK001', '수분 가득 토너', '뷰티브랜드A', 'beauty', 'skincare_toner', 25000, 30000, 16.67, '건조한 피부에 수분을 공급하는 보습 토너'),
('BK002', '진정 에센스', '뷰티브랜드B', 'beauty', 'skincare_essence', 35000, 40000, 12.50, '민감한 피부를 진정시키는 에센스'),
('BK003', '영양 크림', '뷰티브랜드C', 'beauty', 'skincare_cream', 45000, 45000, 0, '깊은 영양을 제공하는 고보습 크림'),
('BK004', '비타민 세럼', '뷰티브랜드A', 'beauty', 'skincare_serum', 55000, 65000, 15.38, '피부 톤 개선을 위한 비타민 세럼'),
('BK005', '수분 선크림', '뷰티브랜드D', 'beauty', 'skincare_sunscreen', 20000, 22000, 9.09, 'SPF50+ PA++++ 수분 선크림')
ON CONFLICT (product_number) DO NOTHING;

-- 샘플 리뷰 데이터 삽입 (테스트용)
INSERT INTO beauty_reviews (
    review_id, product_number, content, rating, created_at, author, 
    like_count, verified_purchase, skin_type, sentiment_score, sentiment_label
) VALUES
('REV001', 'BK001', '정말 보습력이 좋아요! 건조한 제 피부에 딱 맞네요. 끈적임도 없고 흡수도 빨라서 아침에 사용하기 좋습니다.', 5.0, NOW() - INTERVAL '10 days', '사용자A', 25, true, '건성', 5, '긍정'),
('REV002', 'BK001', '가격 대비 괜찮은데 향이 좀 강해요. 무향을 선호하는 분들은 고려하세요.', 4.0, NOW() - INTERVAL '8 days', '사용자B', 12, true, '복합성', 4, '긍정'),
('REV003', 'BK002', '진정 효과는 좋은데 보습력이 조금 아쉬워요. 여름용으로는 좋을 것 같아요.', 3.5, NOW() - INTERVAL '5 days', '사용자C', 8, true, '지성', 3, '중립'),
('REV004', 'BK003', '너무 무겁고 끈적여서 제 피부엔 안 맞았어요. 지성 피부는 피하는 게 좋을 듯.', 2.0, NOW() - INTERVAL '3 days', '사용자D', 5, true, '지성', 2, '부정'),
('REV005', 'BK004', '비타민 세럼 중에 최고예요! 피부 톤이 확실히 밝아졌어요. 추천합니다!', 5.0, NOW() - INTERVAL '2 days', '사용자E', 42, true, '건성', 5, '긍정')
ON CONFLICT (review_id) DO NOTHING;

-- 통계 뷰 생성
CREATE OR REPLACE VIEW product_review_stats AS
SELECT 
    p.product_number,
    p.name,
    p.brand,
    p.category,
    p.price,
    COUNT(r.id) as review_count,
    AVG(r.rating) as avg_rating,
    AVG(r.sentiment_score) as avg_sentiment,
    SUM(CASE WHEN r.sentiment_label = '긍정' THEN 1 ELSE 0 END) as positive_count,
    SUM(CASE WHEN r.sentiment_label = '중립' THEN 1 ELSE 0 END) as neutral_count,
    SUM(CASE WHEN r.sentiment_label = '부정' THEN 1 ELSE 0 END) as negative_count,
    SUM(r.like_count) as total_likes
FROM products p
LEFT JOIN beauty_reviews r ON p.product_number = r.product_number
GROUP BY p.product_number, p.name, p.brand, p.category, p.price;

-- 피부 타입별 통계 뷰
CREATE OR REPLACE VIEW skin_type_stats AS
SELECT 
    product_number,
    skin_type,
    COUNT(*) as review_count,
    AVG(rating) as avg_rating,
    AVG(sentiment_score) as avg_sentiment
FROM beauty_reviews
WHERE skin_type IS NOT NULL
GROUP BY product_number, skin_type;

-- 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- products 테이블에 업데이트 트리거 적용
DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 권한 설정 (필요시 조정)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO n8n_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO n8n_user;

COMMENT ON TABLE products IS '뷰티컬리 제품 정보';
COMMENT ON TABLE beauty_reviews IS '제품 리뷰 및 감정 분석 결과';
COMMENT ON TABLE query_logs IS '사용자 쿼리 및 답변 로그';
