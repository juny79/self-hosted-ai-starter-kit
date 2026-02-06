# Beauty Kurly Shopping Agent - Quick Setup Script
# PowerShell Script for Windows

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "뷰티컬리 쇼핑 에이전트 자동 설정 스크립트" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# 1. 환경 변수 확인
Write-Host "[1/7] 환경 변수 파일 확인 중..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "  ⚠️  .env 파일이 없습니다. .env.example 복사 중..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "  ✅ .env 파일 생성 완료" -ForegroundColor Green
    Write-Host "  📝 .env 파일을 열어 OpenAI API 키를 입력해주세요!" -ForegroundColor Magenta
    Start-Sleep -Seconds 2
} else {
    Write-Host "  ✅ .env 파일 존재" -ForegroundColor Green
}

Write-Host ""

# 2. Docker 상태 확인
Write-Host "[2/7] Docker 상태 확인 중..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "  ✅ Docker 설치됨: $dockerVersion" -ForegroundColor Green
    
    $composeVersion = docker-compose --version
    Write-Host "  ✅ Docker Compose 설치됨: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Docker가 설치되어 있지 않습니다!" -ForegroundColor Red
    Write-Host "  https://www.docker.com/products/docker-desktop 에서 Docker Desktop을 설치하세요." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# 3. Docker Compose 실행
Write-Host "[3/7] Docker 컨테이너 시작 중..." -ForegroundColor Yellow
Write-Host "  (최초 실행 시 이미지 다운로드로 시간이 걸릴 수 있습니다)" -ForegroundColor Gray

try {
    docker-compose up -d
    Write-Host "  ✅ Docker 컨테이너 시작 완료" -ForegroundColor Green
    
    # 컨테이너 시작 대기
    Write-Host "  ⏳ 서비스 초기화 대기 중 (30초)..." -ForegroundColor Gray
    Start-Sleep -Seconds 30
} catch {
    Write-Host "  ❌ Docker 컨테이너 시작 실패!" -ForegroundColor Red
    Write-Host "  오류: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 4. PostgreSQL 스키마 적용
Write-Host "[4/7] PostgreSQL 데이터베이스 스키마 적용 중..." -ForegroundColor Yellow

if (Test-Path "database_schema.sql") {
    try {
        Get-Content "database_schema.sql" | docker-compose exec -T postgres psql -U n8n -d n8n
        Write-Host "  ✅ PostgreSQL 스키마 적용 완료" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  PostgreSQL 스키마 적용 실패 - 수동으로 적용해야 할 수 있습니다" -ForegroundColor Yellow
        Write-Host "  명령어: docker-compose exec -T postgres psql -U n8n -d n8n < database_schema.sql" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠️  database_schema.sql 파일을 찾을 수 없습니다" -ForegroundColor Yellow
}

Write-Host ""

# 5. Qdrant 초기화
Write-Host "[5/7] Qdrant Vector Database 초기화 중..." -ForegroundColor Yellow

# Python이 설치되어 있는지 확인
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✅ Python 설치됨: $pythonVersion" -ForegroundColor Green
    
    if (Test-Path "setup_qdrant.py") {
        Write-Host "  🔧 Qdrant 설정 스크립트 실행 중..." -ForegroundColor Gray
        
        # requests 모듈 확인
        python -c "import requests" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  📦 requests 모듈 설치 중..." -ForegroundColor Gray
            pip install requests -q
        }
        
        # 비대화형 모드로 스크립트 실행 (자동으로 y 응답)
        Write-Host "y`ny" | python setup_qdrant.py
        
        Write-Host "  ✅ Qdrant 초기화 완료" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠️  Python이 설치되어 있지 않습니다. Qdrant는 수동으로 설정해야 합니다." -ForegroundColor Yellow
    Write-Host "  수동 설정 명령어:" -ForegroundColor Gray
    Write-Host "  curl -X PUT 'http://localhost:6333/collections/beauty_reviews' -H 'Content-Type: application/json' -d '{""vectors"": {""size"": 1536, ""distance"": ""Cosine""}}'" -ForegroundColor Gray
}

Write-Host ""

# 6. 서비스 상태 확인
Write-Host "[6/7] 서비스 상태 확인 중..." -ForegroundColor Yellow

$services = @(
    @{Name="n8n"; Port=5678; Url="http://localhost:5678"},
    @{Name="Qdrant"; Port=6333; Url="http://localhost:6333"},
    @{Name="PostgreSQL"; Port=5432; Url="localhost:5432"}
)

foreach ($service in $services) {
    $containerStatus = docker-compose ps $service.Name 2>$null | Select-String "Up"
    if ($containerStatus) {
        Write-Host "  ✅ $($service.Name) - 실행 중" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $($service.Name) - 실행 안 됨" -ForegroundColor Red
    }
}

Write-Host ""

# 7. 워크플로우 파일 확인
Write-Host "[7/7] n8n 워크플로우 파일 확인 중..." -ForegroundColor Yellow

$workflowPath = "n8n\demo-data\workflows\workflow-beauty-kurly-shopping-agent.json"
if (Test-Path $workflowPath) {
    Write-Host "  ✅ 워크플로우 파일 확인됨" -ForegroundColor Green
    Write-Host "  📁 위치: $workflowPath" -ForegroundColor Gray
} else {
    Write-Host "  ❌ 워크플로우 파일을 찾을 수 없습니다!" -ForegroundColor Red
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "🎉 설정 완료!" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# 다음 단계 안내
Write-Host "📋 다음 단계:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. n8n 웹 인터페이스 열기:" -ForegroundColor White
Write-Host "   👉 http://localhost:5678" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. 로그인 정보 (.env 파일에서 확인):" -ForegroundColor White
Write-Host "   - Username: admin (기본값)" -ForegroundColor Gray
Write-Host "   - Password: .env 파일의 N8N_BASIC_AUTH_PASSWORD 참조" -ForegroundColor Gray
Write-Host ""
Write-Host "3. 워크플로우 임포트:" -ForegroundColor White
Write-Host "   - Workflows → Import from File" -ForegroundColor Gray
Write-Host "   - 파일 선택: $workflowPath" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Credentials 설정:" -ForegroundColor White
Write-Host "   - OpenAI API Key 등록" -ForegroundColor Gray
Write-Host "   - PostgreSQL 연결 정보 입력" -ForegroundColor Gray
Write-Host "   - (선택) Slack 연동" -ForegroundColor Gray
Write-Host ""
Write-Host "5. 워크플로우 활성화:" -ForegroundColor White
Write-Host "   - 우측 상단 'Active' 스위치 ON" -ForegroundColor Gray
Write-Host ""
Write-Host "📚 자세한 가이드:" -ForegroundColor Cyan
Write-Host "   BEAUTY_KURLY_WORKFLOW_GUIDE.md 파일 참조" -ForegroundColor Yellow
Write-Host ""
Write-Host "🔧 유용한 명령어:" -ForegroundColor Cyan
Write-Host "   - 로그 확인: docker-compose logs -f n8n" -ForegroundColor Gray
Write-Host "   - 서비스 중지: docker-compose down" -ForegroundColor Gray
Write-Host "   - 서비스 재시작: docker-compose restart" -ForegroundColor Gray
Write-Host ""

# 브라우저 자동 열기 (선택)
$openBrowser = Read-Host "n8n 웹 인터페이스를 브라우저로 여시겠습니까? (Y/N)"
if ($openBrowser -eq "Y" -or $openBrowser -eq "y") {
    Start-Process "http://localhost:5678"
    Write-Host "  ✅ 브라우저 실행됨" -ForegroundColor Green
}

Write-Host ""
Write-Host "Happy Automating! 🚀" -ForegroundColor Magenta
