# Product Insight Agent - Data Management Guide

## Overview

Product Insight Agent의 분석 데이터는 JSON 파일로 관리되며, 스키마 검증을 통해 일관성을 보장합니다.

## 📁 Data Files Structure

```
src/lambda/agents/product-insight/
├── data/
│   ├── industry_data.json    # 16개 업종 데이터
│   ├── region_data.json       # 16개 지역 데이터
│   └── size_data.json         # 3개 규모 데이터
├── data_schema.py             # 스키마 검증 유틸리티
└── index.py                   # Agent 메인 코드
```

## 🔍 JSON Schema Requirements

### Industry Data Schema

**필수 필드 (7개)**:
```json
{
  "industry_name": {
    "characteristics": ["string", "string", "string"],      // 최소 3개
    "success_factors": ["string", "string", "string"],      // 최소 3개
    "market_trends": ["string", "string", "string"],        // 최소 3개
    "risk_factors": ["string", "string", "string"],         // 최소 3개
    "base_score": 75,                                       // number (0-100)
    "growth_potential": "MEDIUM",                           // LOW|MEDIUM|HIGH
    "competition_level": "HIGH"                             // LOW|MEDIUM|HIGH|VERY_HIGH
  }
}
```

**유효한 값**:
- `growth_potential`: `"LOW"`, `"MEDIUM"`, `"HIGH"`
- `competition_level`: `"LOW"`, `"MEDIUM"`, `"HIGH"`, `"VERY_HIGH"`, `"LOW_MEDIUM"`, `"MEDIUM_HIGH"`

### Region Data Schema

**필수 필드 (8개)**:
```json
{
  "region_name": {
    "market_size": "LARGE",                                 // 시장 규모
    "competition_level": "VERY_HIGH",                       // 경쟁 수준
    "consumer_power": "HIGH",                               // 소비력
    "rent_cost": "VERY_HIGH",                               // 임대료
    "characteristics": ["string", "string", "string"],      // 최소 3개
    "advantages": ["string", "string", "string"],           // 최소 3개
    "challenges": ["string", "string", "string"],           // 최소 3개
    "score_modifier": 10                                    // number (-10 ~ +10)
  }
}
```

**유효한 값**:
- `market_size`: `"SMALL"`, `"MEDIUM"`, `"LARGE"`, `"VERY_LARGE"`, `"SMALL_MEDIUM"`, `"MEDIUM_LARGE"`
- `competition_level`: `"LOW"`, `"MEDIUM"`, `"HIGH"`, `"VERY_HIGH"`, `"LOW_MEDIUM"`, `"MEDIUM_HIGH"`
- `consumer_power`: `"LOW"`, `"MEDIUM"`, `"HIGH"`, `"VERY_HIGH"`, `"LOW_MEDIUM"`, `"MEDIUM_HIGH"`
- `rent_cost`: `"LOW"`, `"MEDIUM"`, `"HIGH"`, `"VERY_HIGH"`, `"LOW_MEDIUM"`, `"MEDIUM_HIGH"`

### Size Data Schema

**필수 필드 (8개)**:
```json
{
  "size_name": {
    "characteristics": ["string", "string", "string"],      // 최소 3개
    "advantages": ["string", "string", "string"],           // 최소 3개
    "challenges": ["string", "string", "string"],           // 최소 3개
    "strategies": ["string", "string", "string"],           // 최소 3개
    "investment_range": "1천만원 - 5천만원",                // string
    "employee_range": "1-5명",                              // string
    "score_modifier": -5,                                   // number (-10 ~ +10)
    "risk_level": "MEDIUM_HIGH"                             // 리스크 수준
  }
}
```

**유효한 값**:
- `risk_level`: `"LOW"`, `"MEDIUM"`, `"HIGH"`, `"LOW_MEDIUM"`, `"MEDIUM_HIGH"`

## ✅ Schema Validation

### Automatic Validation

Agent 초기화 시 자동으로 JSON 파일을 로드하고 검증합니다:

```python
from index import ProductInsightAgent

# JSON 파일 자동 로드 및 검증
agent = ProductInsightAgent()

# 로그 출력:
# INFO - Loaded industry_data.json from JSON file
# INFO - Loaded region_data.json from JSON file
# INFO - Loaded size_data.json from JSON file
```

### Manual Validation

스키마 검증 스크립트 실행:

```bash
python3 scripts/validate-data-schema.py
```

**출력 예시**:
```
✓ industry_data.json exists
✓ region_data.json exists
✓ size_data.json exists

✓ Valid schema
✓ 16 industries loaded
✓ 16 regions loaded
✓ 3 sizes loaded

✓ ALL VALIDATIONS PASSED
```

### Programmatic Validation

Python 코드에서 직접 검증:

```python
from data_schema import (
    DataSchemaValidator,
    load_industry_data,
    load_region_data,
    load_size_data
)

# 개별 파일 검증
industry_data = load_industry_data('data/industry_data.json')
region_data = load_region_data('data/region_data.json')
size_data = load_size_data('data/size_data.json')

# 전체 검증
is_valid, errors = DataSchemaValidator.validate_all_data_files(
    industry_data,
    region_data,
    size_data
)

if not is_valid:
    for data_type, error_list in errors.items():
        print(f"{data_type} errors:")
        for error in error_list:
            print(f"  - {error}")
```

## 🔄 Fallback Mechanism

JSON 파일을 로드할 수 없는 경우, Agent는 자동으로 하드코딩된 fallback 데이터를 사용합니다:

```python
def _load_json_data(self, filename: str, fallback_method: callable):
    """Load data from JSON file with fallback"""
    try:
        # JSON 파일 로드 시도
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.logger.info(f"Loaded {filename} from JSON file")
            return data
    except Exception as e:
        # 실패 시 fallback 데이터 사용
        self.logger.error(f"Failed to load {filename}, using fallback data")
        return fallback_method()
```

**Fallback 시나리오**:
1. JSON 파일이 없는 경우
2. JSON 파일이 손상된 경우
3. 파일 읽기 권한이 없는 경우

## 📝 Data Modification Guide

### 1. 새로운 업종 추가

**industry_data.json**에 추가:

```json
{
  "new_industry": {
    "characteristics": [
      "특성 1",
      "특성 2",
      "특성 3"
    ],
    "success_factors": [
      "성공 요인 1",
      "성공 요인 2",
      "성공 요인 3"
    ],
    "market_trends": [
      "트렌드 1",
      "트렌드 2",
      "트렌드 3"
    ],
    "risk_factors": [
      "리스크 1",
      "리스크 2",
      "리스크 3"
    ],
    "base_score": 75,
    "growth_potential": "MEDIUM",
    "competition_level": "HIGH"
  }
}
```

### 2. 기존 데이터 수정

1. JSON 파일 직접 수정
2. 스키마 검증 실행
3. Agent 재시작

```bash
# 1. JSON 파일 수정
vim src/lambda/agents/product-insight/data/industry_data.json

# 2. 스키마 검증
python3 scripts/validate-data-schema.py

# 3. Agent 테스트
python3 scripts/validate-product-insight-bedrock.py
```

### 3. 데이터 일괄 업데이트

Python 스크립트로 일괄 업데이트:

```python
import json

# 데이터 로드
with open('data/industry_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 모든 base_score에 +5 추가
for industry in data.values():
    industry['base_score'] += 5

# 저장
with open('data/industry_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 검증
from data_schema import load_industry_data
validated_data = load_industry_data('data/industry_data.json')
print("✓ Data updated and validated")
```

## 🚨 Common Errors

### Error 1: Missing Required Field

```
industry.restaurant: Missing required field 'base_score'
```

**해결**: 누락된 필드 추가

```json
{
  "restaurant": {
    ...
    "base_score": 75  // 추가
  }
}
```

### Error 2: Invalid Field Type

```
industry.restaurant.base_score: Expected type <class 'int'>, got <class 'str'>
```

**해결**: 타입 수정

```json
{
  "base_score": 75  // ✓ 올바름
  "base_score": "75"  // ✗ 잘못됨
}
```

### Error 3: List Too Short

```
industry.restaurant.characteristics: List must have at least 3 items, got 2
```

**해결**: 리스트 항목 추가

```json
{
  "characteristics": [
    "특성 1",
    "특성 2",
    "특성 3"  // 최소 3개 필요
  ]
}
```

### Error 4: Invalid Enum Value

```
industry.restaurant.growth_potential: Invalid value 'SUPER_HIGH'. Must be one of ['LOW', 'MEDIUM', 'HIGH']
```

**해결**: 유효한 값 사용

```json
{
  "growth_potential": "HIGH"  // ✓ 올바름
  "growth_potential": "SUPER_HIGH"  // ✗ 잘못됨
}
```

## 🔧 Maintenance

### Regular Checks

1. **월간 데이터 검증**
   ```bash
   python3 scripts/validate-data-schema.py
   ```

2. **데이터 백업**
   ```bash
   cp -r src/lambda/agents/product-insight/data data_backup_$(date +%Y%m%d)
   ```

3. **버전 관리**
   - JSON 파일을 Git으로 관리
   - 변경 사항 커밋 시 검증 스크립트 실행

### Best Practices

1. **JSON 포맷 유지**
   - 들여쓰기: 2 spaces
   - UTF-8 인코딩
   - 한글 문자 그대로 저장 (`ensure_ascii=False`)

2. **스키마 일관성**
   - 모든 항목이 동일한 필드 구조 유지
   - 리스트 최소 길이 준수 (3개 이상)
   - 유효한 enum 값만 사용

3. **테스트**
   - 데이터 수정 후 반드시 검증
   - Agent 테스트로 실제 동작 확인
   - 프로덕션 배포 전 스테이징 테스트

## 📊 Data Statistics

### Current Data

- **Industries**: 16개
  - restaurant, retail, service, healthcare, education, technology, manufacturing, construction, finance, beauty, fitness, entertainment, automotive, agriculture, logistics, other

- **Regions**: 16개
  - seoul, busan, daegu, incheon, gwangju, daejeon, ulsan, gyeonggi, gangwon, chungbuk, chungnam, jeonbuk, jeonnam, gyeongbuk, gyeongnam, jeju

- **Sizes**: 3개
  - small, medium, large

### Schema Compliance

- ✅ All 16 industries: 100% compliant
- ✅ All 16 regions: 100% compliant
- ✅ All 3 sizes: 100% compliant

## 🎯 Benefits of JSON-based Data Management

### 1. **Easy Maintenance** 🔧
- JSON 파일 직접 수정 가능
- 코드 재배포 없이 데이터 업데이트
- 버전 관리 용이

### 2. **Schema Validation** ✅
- 자동 스키마 검증
- 일관성 보장
- 오류 조기 발견

### 3. **Fallback Safety** 🛡️
- JSON 로드 실패 시 자동 fallback
- 서비스 중단 없음
- 안정적인 운영

### 4. **Scalability** 📈
- 새로운 업종/지역 쉽게 추가
- 데이터 구조 확장 가능
- 다국어 지원 준비

## 🚀 Future Enhancements

1. **S3 Integration**
   - JSON 파일을 S3에 저장
   - 동적 데이터 업데이트
   - 버전 관리 자동화

2. **Admin UI**
   - 웹 기반 데이터 편집 인터페이스
   - 실시간 검증
   - 변경 이력 추적

3. **Multi-language Support**
   - 영어, 일본어 등 다국어 데이터
   - 언어별 JSON 파일
   - 자동 번역 통합

---

**Last Updated**: 2025-10-09  
**Version**: 2.1.0  
**Status**: Production Ready ✅
