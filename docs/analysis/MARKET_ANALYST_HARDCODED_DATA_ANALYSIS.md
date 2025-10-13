# Market Analyst Agent - 하드코딩 데이터 분석 및 DynamoDB 설계

## 분석 일자
2025-10-13

## 하드코딩된 데이터 목록

### 1. 소비자 선호도 데이터 (Consumer Preferences)

#### 1.1 세대별 선호도 (`generational_preferences`)
**위치**: `_analyze_consumer_preferences()` 메서드
**데이터 구조**:
```python
{
    "MZ세대": {
        "priorities": ["경험", "가치 소비", "개성", "편의성"],
        "spending_pattern": "선택적 집중",
        "decision_factors": ["SNS 후기", "브랜드 가치", "개인화"],
        "growth_rate": "+25%"
    },
    "X세대": {...},
    "베이비부머": {...}
}
```
**특성**: 
- 정적 참조 데이터
- 업데이트 빈도: 낮음 (연 1-2회)
- **권장**: JSON 파일로 분리

#### 1.2 지역별 선호도 (`regional_preferences`)
**위치**: `_analyze_consumer_preferences()` 메서드
**데이터 구조**:
```python
{
    "seoul": ["트렌디함", "혁신성", "브랜드 가치", "차별화"],
    "busan": ["실용성", "가성비", "지역 특색", "편안함"],
    "gyeonggi": ["가족 친화", "편의성", "안전성", "실용성"],
    "jeju": ["자연 친화", "힐링", "특별함", "지속가능성"]
}
```
**특성**:
- 정적 참조 데이터
- 업데이트 빈도: 낮음
- **권장**: JSON 파일로 분리

#### 1.3 업종별 소비자 행동 변화 (`behavioral_changes`)
**위치**: `_analyze_consumer_preferences()` 메서드
**데이터 구조**:
```python
{
    "restaurant": [
        {"change": "배달 앱 사용 증가", "percentage": "+78%"},
        {"change": "건강 메뉴 선호", "percentage": "+45%"},
        ...
    ],
    "retail": [...],
    "service": [...]
}
```
**특성**:
- 동적 데이터 (트렌드 변화)
- 업데이트 빈도: 높음 (월 1회)
- **권장**: DynamoDB 테이블

---

### 2. 위험 분석 데이터 (Risk Analysis)

#### 2.1 트렌드 변화 위험 (`trend_risks`)
**위치**: `_analyze_trend_risks()` 메서드
**데이터 구조**:
```python
[
    {
        "risk": "트렌드 급변",
        "probability": "중간",
        "impact": "높음",
        "description": "소비자 트렌드의 급격한 변화",
        "mitigation": "다양한 트렌드 모니터링 및 빠른 적응"
    },
    ...
]
```
**특성**:
- 정적 참조 데이터
- 업데이트 빈도: 낮음
- **권장**: JSON 파일로 분리

#### 2.2 업종별 특화 위험 (`industry_specific_risks`)
**위치**: `_analyze_trend_risks()` 메서드
**데이터 구조**:
```python
{
    "restaurant": [
        {"risk": "식자재 가격 변동", "impact": "높음"},
        {"risk": "배달비 상승", "impact": "중간"},
        ...
    ],
    "retail": [...],
    "technology": [...]
}
```
**특성**:
- 동적 데이터 (시장 상황 변화)
- 업데이트 빈도: 중간 (분기 1회)
- **권장**: DynamoDB 테이블

---

### 3. 경쟁 분석 데이터 (Competitive Analysis)

#### 3.1 진입 장벽 (`barriers_data`)
**위치**: `_analyze_entry_barriers()` 메서드
**데이터 구조**:
```python
{
    "restaurant": [
        {"barrier": "초기 투자비", "level": "중간", "description": "인테리어, 장비 비용"},
        {"barrier": "위치 선정", "level": "높음", "description": "임대료, 유동인구"},
        ...
    ],
    "retail": [...],
    "service": [...],
    "healthcare": [...],
    "education": [...],
    "technology": [...]
}
```
**특성**:
- 정적 참조 데이터
- 업데이트 빈도: 낮음
- **권장**: JSON 파일로 분리

#### 3.2 차별화 요소 (`factors`)
**위치**: `_get_differentiation_factors()` 메서드
**데이터 구조**:
```python
{
    "restaurant": ["독특한 메뉴", "분위기", "서비스 품질", "가성비"],
    "retail": ["상품 큐레이션", "고객 서비스", "매장 경험", "전문성"],
    ...
}
```
**특성**:
- 정적 참조 데이터
- 업데이트 빈도: 낮음
- **권장**: JSON 파일로 분리

#### 3.3 벤치마크 지표 (`metrics`)
**위치**: `_get_benchmark_metrics()` 메서드
**데이터 구조**:
```python
{
    "restaurant": {
        "고객 재방문율": "60-70%",
        "평균 객단가": "15,000-25,000원",
        "월 매출": "3,000-8,000만원"
    },
    ...
}
```
**특성**:
- 동적 데이터 (시장 변화)
- 업데이트 빈도: 중간 (분기 1회)
- **권장**: DynamoDB 테이블

---

### 4. 기회 분석 데이터 (Opportunity Analysis)

#### 4.1 시장 갭 (`gaps`)
**위치**: `_identify_market_gaps()` 메서드
**데이터 구조**:
```python
{
    "restaurant": [
        {"gap": "건강한 야식 옵션", "size": "중간", "difficulty": "낮음"},
        {"gap": "1인 가구 맞춤 메뉴", "size": "높음", "difficulty": "중간"},
        ...
    ],
    ...
}
```
**특성**:
- 동적 데이터 (트렌드 변화)
- 업데이트 빈도: 높음 (월 1회)
- **권장**: DynamoDB 테이블

#### 4.2 신규 고객 세그먼트 (`segments`)
**위치**: `_identify_new_segments()` 메서드
**데이터 구조**:
```python
[
    {
        "segment": "디지털 네이티브 시니어",
        "size": "증가 중",
        "characteristics": "기술 친화적 50-60대",
        "opportunity": "높음"
    },
    ...
]
```
**특성**:
- 동적 데이터 (인구 통계 변화)
- 업데이트 빈도: 중간 (분기 1회)
- **권장**: DynamoDB 테이블

#### 4.3 기술 기회 (`opportunities`)
**위치**: `_identify_tech_opportunities()` 메서드
**데이터 구조**:
```python
{
    "restaurant": [
        {"tech": "AI 메뉴 추천", "maturity": "중간", "impact": "높음"},
        {"tech": "무인 주문 시스템", "maturity": "높음", "impact": "중간"},
        ...
    ],
    ...
}
```
**특성**:
- 동적 데이터 (기술 발전)
- 업데이트 빈도: 높음 (월 1회)
- **권장**: DynamoDB 테이블

#### 4.4 파트너십 기회 (`partnerships`)
**위치**: `_identify_partnership_opportunities()` 메서드
**데이터 구조**:
```python
[
    {
        "type": "기술 파트너십",
        "partner": "IT 스타트업",
        "benefit": "디지털 전환 가속화",
        "feasibility": "높음"
    },
    ...
]
```
**특성**:
- 정적 참조 데이터
- 업데이트 빈도: 낮음
- **권장**: JSON 파일로 분리

#### 4.5 확장 기회 (`opportunities`)
**위치**: `_identify_expansion_opportunities()` 메서드
**데이터 구조**:
```python
[
    {
        "type": "지역 확장",
        "target": "인근 지역",
        "timeline": "6-12개월",
        "investment": "중간"
    },
    ...
]
```
**특성**:
- 정적 참조 데이터
- 업데이트 빈도: 낮음
- **권장**: JSON 파일로 분리

---

### 5. 인사이트 데이터 (Insights)

#### 5.1 선호도 변화 인사이트 (`insights`)
**위치**: `_extract_preference_insights()` 메서드
**데이터 구조**:
```python
{
    "restaurant": [
        "건강과 맛의 균형 추구",
        "개인화된 다이닝 경험 선호",
        "지속가능성 고려 증가",
        "소셜미디어 공유 가치 중시"
    ],
    ...
}
```
**특성**:
- 동적 데이터 (트렌드 변화)
- 업데이트 빈도: 높음 (월 1회)
- **권장**: DynamoDB 테이블

#### 5.2 미래 선호도 전망
**위치**: `_project_future_preferences()` 메서드
**데이터 구조**:
```python
{
    "timeframe": "2025-2027",
    "keyChanges": [
        "AI 기반 개인화 서비스 확산",
        "지속가능성 중시 확대",
        ...
    ],
    "impactLevel": "높음"
}
```
**특성**:
- 동적 데이터 (예측 모델)
- 업데이트 빈도: 중간 (분기 1회)
- **권장**: DynamoDB 테이블

---

### 6. 트렌드 데이터 (Trend Data)

#### 6.1 업종별 특화 트렌드 (`industry_trends`)
**위치**: `_get_fallback_trend_data()` 메서드
**데이터 구조**:
```python
{
    "restaurant": [
        {"trend": "배달/테이크아웃 확산", "growth": "+25%"},
        {"trend": "건강식 메뉴 선호", "growth": "+18%"},
        ...
    ],
    ...
}
```
**특성**:
- 동적 데이터 (트렌드 변화)
- 업데이트 빈도: 높음 (월 1회)
- **권장**: DynamoDB 테이블 (이미 market_data_loader 사용 중)

---

## 데이터 분류 요약

### JSON 파일로 분리 (정적 참조 데이터)
1. ✅ 세대별 선호도 (`generational_preferences`)
2. ✅ 지역별 선호도 (`regional_preferences`)
3. ✅ 트렌드 변화 위험 (`trend_risks`)
4. ✅ 진입 장벽 (`barriers_data`)
5. ✅ 차별화 요소 (`differentiation_factors`)
6. ✅ 파트너십 기회 (`partnership_opportunities`)
7. ✅ 확장 기회 (`expansion_opportunities`)

**총 7개 JSON 파일**

### DynamoDB 테이블로 이관 (동적 데이터)
1. ✅ 업종별 소비자 행동 변화 (`behavioral_changes`)
2. ✅ 업종별 특화 위험 (`industry_specific_risks`)
3. ✅ 벤치마크 지표 (`benchmark_metrics`)
4. ✅ 시장 갭 (`market_gaps`)
5. ✅ 신규 고객 세그먼트 (`new_segments`)
6. ✅ 기술 기회 (`tech_opportunities`)
7. ✅ 선호도 변화 인사이트 (`preference_insights`)
8. ✅ 미래 선호도 전망 (`future_projections`)

**총 8개 DynamoDB 테이블 (또는 단일 테이블 설계)**

---

## DynamoDB 테이블 설계 제안

### 옵션 1: 단일 테이블 설계 (Single Table Design) - 권장

#### 테이블명: `MarketAnalysisData`

**Primary Key**:
- `PK` (Partition Key): `DATA_TYPE#INDUSTRY` (예: `BEHAVIORAL_CHANGES#restaurant`)
- `SK` (Sort Key): `REGION#TIMESTAMP` (예: `seoul#2025-10-13` 또는 `GLOBAL#2025-10-13`)

**GSI (Global Secondary Index)**:
- `GSI1PK`: `DATA_TYPE` (모든 업종의 동일 데이터 타입 조회)
- `GSI1SK`: `TIMESTAMP` (최신 데이터 조회)

**속성**:
```json
{
  "PK": "BEHAVIORAL_CHANGES#restaurant",
  "SK": "seoul#2025-10-13",
  "dataType": "behavioral_changes",
  "industry": "restaurant",
  "region": "seoul",
  "data": {
    "changes": [
      {"change": "배달 앱 사용 증가", "percentage": "+78%"},
      ...
    ]
  },
  "lastUpdated": "2025-10-13T12:00:00Z",
  "version": "1.0",
  "ttl": 1735689600  // 1년 후 자동 삭제
}
```

**장점**:
- 단일 테이블로 모든 데이터 관리
- 효율적인 쿼리 패턴
- 비용 절감 (테이블 1개)

**단점**:
- 복잡한 데이터 모델링
- 초기 설계 난이도 높음

---

### 옵션 2: 다중 테이블 설계 (Multiple Tables) - 단순함

#### 테이블 목록:

1. **`BehavioralChanges`**
   - PK: `industry`
   - SK: `region#timestamp`
   - 데이터: 소비자 행동 변화

2. **`IndustryRisks`**
   - PK: `industry`
   - SK: `risk_type#timestamp`
   - 데이터: 업종별 위험 요소

3. **`BenchmarkMetrics`**
   - PK: `industry`
   - SK: `metric_type#timestamp`
   - 데이터: 벤치마크 지표

4. **`MarketGaps`**
   - PK: `industry`
   - SK: `region#timestamp`
   - 데이터: 시장 갭 분석

5. **`CustomerSegments`**
   - PK: `segment_id`
   - SK: `timestamp`
   - 데이터: 신규 고객 세그먼트

6. **`TechOpportunities`**
   - PK: `industry`
   - SK: `tech_category#timestamp`
   - 데이터: 기술 기회

7. **`PreferenceInsights`**
   - PK: `industry`
   - SK: `region#timestamp`
   - 데이터: 선호도 인사이트

8. **`FutureProjections`**
   - PK: `industry`
   - SK: `timeframe#timestamp`
   - 데이터: 미래 전망

**장점**:
- 명확한 데이터 분리
- 이해하기 쉬움
- 독립적 관리 가능

**단점**:
- 테이블 수 증가 (비용 증가)
- 여러 테이블 쿼리 필요

---

## 권장 사항

### 1단계: JSON 파일 분리 (즉시 실행 가능)
- 정적 데이터 7개를 JSON 파일로 분리
- `src/lambda/agents/market-analyst/data/` 디렉토리 생성
- 코드 수정: JSON 파일 로드 로직 추가

### 2단계: DynamoDB 단일 테이블 설계 (중기 계획)
- `MarketAnalysisData` 테이블 생성
- 동적 데이터 8개를 DynamoDB로 이관
- 초기 데이터 로딩 스크립트 작성
- Lambda 코드 수정: DynamoDB 쿼리 로직 추가

### 3단계: 데이터 업데이트 파이프라인 구축 (장기 계획)
- EventBridge 스케줄러로 정기 업데이트
- Step Functions로 데이터 수집 워크플로
- Bedrock Claude로 트렌드 분석 자동화

---

## 예상 효과

### 코드 품질 개선
- ✅ 하드코딩 제거 → 유지보수성 향상
- ✅ 데이터와 로직 분리 → 가독성 향상
- ✅ 테스트 용이성 증가

### 운영 효율성
- ✅ 데이터 업데이트 시 코드 재배포 불필요
- ✅ 실시간 데이터 반영 가능
- ✅ A/B 테스트 및 실험 용이

### 비용 최적화
- ✅ DynamoDB On-Demand 모드 사용 시 사용량 기반 과금
- ✅ TTL 설정으로 오래된 데이터 자동 삭제
- ✅ Lambda 실행 시간 단축 (JSON 로드 vs 하드코딩)

---

## 다음 단계

1. **JSON 파일 분리 작업 진행 여부 확인**
2. **DynamoDB 테이블 설계 방식 선택 (단일 vs 다중)**
3. **구현 우선순위 결정**

진행하시겠습니까?
