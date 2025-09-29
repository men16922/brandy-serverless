# API 사용 예시 📡

## 🎯 실제 API 호출 흐름

사용자가 "서울 강남에서 소규모 카페를 운영하려고 합니다"라고 입력했을 때의 전체 과정을 보여드립니다.

## 1단계: 세션 생성

### 요청
```bash
curl -X POST http://localhost:3000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "businessInfo": {
      "industry": "restaurant",
      "region": "seoul", 
      "size": "small",
      "description": "강남에서 운영할 소규모 카페"
    }
  }'
```

### 응답
```json
{
  "sessionId": "abc123-def456-ghi789",
  "status": "active",
  "currentStep": 1,
  "message": "세션이 생성되었습니다. 비즈니스 분석을 시작합니다."
}
```

## 2단계: 비즈니스 분석 요청

### 요청
```bash
curl -X POST http://localhost:3000/analysis \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "abc123-def456-ghi789"
  }'
```

### 응답
```json
{
  "sessionId": "abc123-def456-ghi789",
  "status": "processing",
  "currentStep": 1,
  "message": "비즈니스 분석 중입니다...",
  "estimatedTime": "30초"
}
```

## 3단계: 분석 결과 확인

### 요청
```bash
curl -X GET http://localhost:3000/sessions/abc123-def456-ghi789
```

### 응답 (분석 완료 후)
```json
{
  "sessionId": "abc123-def456-ghi789",
  "status": "active",
  "currentStep": 2,
  "businessInfo": {
    "industry": "restaurant",
    "region": "seoul",
    "size": "small",
    "description": "강남에서 운영할 소규모 카페"
  },
  "analysisResult": {
    "summary": "강남 지역은 높은 유동인구와 구매력을 가진 지역으로 카페 사업에 유리합니다.",
    "score": 85.5,
    "insights": [
      "강남역 주변 직장인 고객층 타겟 가능",
      "프리미엄 원두 및 디저트 메뉴 선호도 높음",
      "배달 서비스 수요 증가 추세"
    ],
    "marketTrends": [
      "스페셜티 커피 시장 성장",
      "인스타그램 친화적 인테리어 선호",
      "친환경 포장재 사용 트렌드"
    ],
    "recommendations": [
      "고품질 원두 사용으로 차별화",
      "SNS 마케팅 활용",
      "배달 앱 입점 고려"
    ]
  }
}
```

## 4단계: 상호명 제안 요청

### 요청
```bash
curl -X POST http://localhost:3000/names/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "abc123-def456-ghi789"
  }'
```

### 응답
```json
{
  "sessionId": "abc123-def456-ghi789",
  "status": "active", 
  "currentStep": 3,
  "businessNames": {
    "suggestions": [
      {
        "name": "카페 모닝글로우",
        "description": "아침의 따뜻한 빛을 연상시키는 친근한 이름",
        "pronunciationScore": 92.0,
        "searchScore": 88.0,
        "overallScore": 90.0
      },
      {
        "name": "브루잉 스테이션",
        "description": "전문적인 커피 추출을 강조하는 모던한 이름",
        "pronunciationScore": 85.0,
        "searchScore": 91.0,
        "overallScore": 88.0
      },
      {
        "name": "원두향",
        "description": "커피의 본질을 담은 간결하고 기억하기 쉬운 이름",
        "pronunciationScore": 95.0,
        "searchScore": 82.0,
        "overallScore": 88.5
      }
    ],
    "selectedName": null,
    "regenerationCount": 0,
    "maxRegenerations": 3
  }
}
```

## 5단계: 간판 디자인 생성 요청

### 요청
```bash
curl -X POST http://localhost:3000/signboards/generate \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "abc123-def456-ghi789",
    "selectedName": "카페 모닝글로우"
  }'
```

### 응답 (생성 중)
```json
{
  "sessionId": "abc123-def456-ghi789",
  "status": "processing",
  "currentStep": 3,
  "message": "간판 디자인을 생성 중입니다. 3개의 AI가 동시에 작업하고 있습니다.",
  "estimatedTime": "60초"
}
```

### 응답 (생성 완료 후)
```json
{
  "sessionId": "abc123-def456-ghi789",
  "status": "active",
  "currentStep": 4,
  "signboardImages": {
    "images": [
      {
        "url": "https://localhost:9000/signboards/abc123-dalle-001.png",
        "provider": "dalle",
        "style": "modern",
        "prompt": "Modern cafe signboard with 'Cafe Morning Glow' text, warm lighting, minimalist design",
        "generatedAt": "2024-01-15T10:30:00Z",
        "isFallback": false
      },
      {
        "url": "https://localhost:9000/signboards/abc123-sdxl-001.png", 
        "provider": "sdxl",
        "style": "vintage",
        "prompt": "Vintage style cafe signboard 'Cafe Morning Glow', wooden texture, retro fonts",
        "generatedAt": "2024-01-15T10:30:15Z",
        "isFallback": false
      },
      {
        "url": "https://localhost:9000/signboards/abc123-gemini-001.png",
        "provider": "gemini", 
        "style": "elegant",
        "prompt": "Elegant cafe signboard design for 'Cafe Morning Glow', gold accents, sophisticated typography",
        "generatedAt": "2024-01-15T10:30:30Z",
        "isFallback": false
      }
    ],
    "selectedImageUrl": null
  }
}
```

## 6단계: 인테리어 추천 요청

### 요청
```bash
curl -X POST http://localhost:3000/interiors/generate \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "abc123-def456-ghi789",
    "selectedSignboardUrl": "https://localhost:9000/signboards/abc123-dalle-001.png"
  }'
```

### 응답
```json
{
  "sessionId": "abc123-def456-ghi789",
  "status": "active",
  "currentStep": 5,
  "interiorImages": {
    "images": [
      {
        "url": "https://localhost:9000/interiors/abc123-interior-001.png",
        "provider": "dalle",
        "style": "modern-minimalist",
        "prompt": "Modern minimalist cafe interior matching morning glow theme, warm wood tones, natural lighting",
        "generatedAt": "2024-01-15T10:35:00Z",
        "isFallback": false
      },
      {
        "url": "https://localhost:9000/interiors/abc123-interior-002.png",
        "provider": "dalle", 
        "style": "cozy-industrial",
        "prompt": "Cozy industrial cafe interior with exposed brick, warm lighting, comfortable seating",
        "generatedAt": "2024-01-15T10:35:15Z",
        "isFallback": false
      },
      {
        "url": "https://localhost:9000/interiors/abc123-interior-003.png",
        "provider": "dalle",
        "style": "scandinavian",
        "prompt": "Scandinavian style cafe interior, light wood, plants, clean lines, hygge atmosphere",
        "generatedAt": "2024-01-15T10:35:30Z", 
        "isFallback": false
      }
    ],
    "selectedImageUrl": null,
    "budgetRange": "3000-5000만원",
    "colorPalette": ["#F5F5DC", "#8B4513", "#228B22", "#FFFFFF"]
  }
}
```

## 7단계: PDF 보고서 생성

### 요청
```bash
curl -X POST http://localhost:3000/report/generate \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "abc123-def456-ghi789"
  }'
```

### 응답
```json
{
  "sessionId": "abc123-def456-ghi789",
  "status": "completed",
  "currentStep": 5,
  "pdfReportPath": "https://localhost:9000/reports/abc123-branding-report.pdf",
  "message": "브랜딩 보고서가 완성되었습니다!"
}
```

## 8단계: 최종 보고서 다운로드

### 요청
```bash
curl -X GET http://localhost:3000/report/url/abc123-def456-ghi789
```

### 응답
```json
{
  "sessionId": "abc123-def456-ghi789",
  "downloadUrl": "https://localhost:9000/reports/abc123-branding-report.pdf?expires=1642248000",
  "expiresAt": "2024-01-15T12:00:00Z",
  "fileSize": "2.5MB",
  "pages": 12
}
```

## 🔍 실제 데이터 확인 방법

### 1. DynamoDB Admin UI에서 세션 데이터 확인
```
http://localhost:8002
→ Tables → branding-chatbot-sessions-local 
→ 세션 ID로 검색하여 전체 진행 상황 확인
```

### 2. MinIO Console에서 생성된 파일 확인
```
http://localhost:9001 (minioadmin/minioadmin)
→ Buckets → ai-branding-chatbot-assets-local
→ signboards/, interiors/, reports/ 폴더에서 생성된 이미지/PDF 확인
```

### 3. 에이전트 실행 로그 확인
```json
{
  "agentLogs": [
    {
      "agent": "supervisor",
      "tool": "workflow.monitor", 
      "latencyMs": 250,
      "status": "success",
      "timestamp": "2024-01-15T10:25:00Z"
    },
    {
      "agent": "product_insight",
      "tool": "kb.search",
      "latencyMs": 1500,
      "status": "success", 
      "timestamp": "2024-01-15T10:25:30Z"
    },
    {
      "agent": "market_analyst", 
      "tool": "market.analyze",
      "latencyMs": 2200,
      "status": "success",
      "timestamp": "2024-01-15T10:26:00Z"
    }
  ]
}
```

## 🧪 테스트 시나리오

### 로컬에서 전체 워크플로 테스트
```bash
# 1. 환경 시작
./scripts/dev.sh setup

# 2. API 서버 시작  
./scripts/dev.sh api

# 3. 다른 터미널에서 API 호출 테스트
curl -X POST http://localhost:3000/sessions \
  -H "Content-Type: application/json" \
  -d '{"businessInfo": {"industry": "restaurant", "region": "seoul", "size": "small"}}'

# 4. DynamoDB Admin UI에서 데이터 확인
open http://localhost:8002

# 5. MinIO Console에서 파일 확인  
open http://localhost:9001
```

이렇게 실제 API를 호출하면서 각 단계별로 어떤 데이터가 생성되고 저장되는지 확인할 수 있습니다! 😊