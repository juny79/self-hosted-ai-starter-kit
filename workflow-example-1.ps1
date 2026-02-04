# n8n 워크플로우 생성 예제 1: HTTP 요청
# HTTP 요청으로 GitHub API 데이터 조회

$apiKey = $env:N8N_API_KEY
$headers = @{"X-N8N-API-KEY" = $apiKey}

$workflow = @{
    name = "GitHub Repository Checker"
    nodes = @(
        @{
            id = "1"
            type = "n8n-nodes-base.start"
            position = @(250, 300)
            parameters = @{}
        },
        @{
            id = "2"
            type = "n8n-nodes-base.httpRequest"
            position = @(450, 300)
            parameters = @{
                url = "https://api.github.com/repos/n8n-io/n8n"
                method = "GET"
                headers = @{
                    "User-Agent" = "n8n Workflow"
                }
            }
        },
        @{
            id = "3"
            type = "n8n-nodes-base.set"
            position = @(650, 300)
            parameters = @{
                assignments = @(
                    @{
                        name = "repository_name"
                        value = "={{ $json.name }}"
                    },
                    @{
                        name = "stars"
                        value = "={{ $json.stargazers_count }}"
                    }
                )
            }
        }
    )
    connections = @{
        "1" = @{
            main = @(
                @(
                    @{
                        node = "2"
                        type = "main"
                        index = 0
                    }
                )
            )
        }
        "2" = @{
            main = @(
                @(
                    @{
                        node = "3"
                        type = "main"
                        index = 0
                    }
                )
            )
        }
    }
    active = $true
} | ConvertTo-Json -Depth 10

# 워크플로우 생성
$response = Invoke-WebRequest `
    -Uri "http://localhost:5678/api/v1/workflows" `
    -Method POST `
    -Headers $headers `
    -Body $workflow `
    -ContentType "application/json" `
    -UseBasicParsing

$result = $response.Content | ConvertFrom-Json
Write-Host "✅ 워크플로우 생성됨!" -ForegroundColor Green
Write-Host "ID: $($result.id)"
Write-Host "Name: $($result.name)"
Write-Host "웹 UI에서 확인: http://localhost:5678/workflows/$($result.id)"
