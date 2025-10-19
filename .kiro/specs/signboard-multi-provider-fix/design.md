# Design Document

## Overview

This design addresses three critical issues in the signboard generation system:
1. **Selection API Mismatch**: The Streamlit app calls `/signboards/select` but the Lambda handler doesn't properly route this action
2. **Provider Distribution**: All images use SDXL instead of distributing across DALL-E, Gemini, and SDXL
3. **English Text Display**: Business names need to be translated to English for better AI image generation results

## Architecture

### Component Interaction Flow

```
User clicks "이 디자인 선택"
    ↓
Streamlit: select_signboard_image(image_url)
    ↓
POST /signboards/select
    ↓
API Gateway → Lambda (Signboard Agent)
    ↓
Lambda: action='select' → _handle_image_selection()
    ↓
DynamoDB: Update session with selected_image_url
    ↓
Response: 200 OK with nextStep='interior'
```

### Provider Distribution Strategy

```
Generate 3 signboard images:
    ↓
Style 1 (modern) → DALL-E Provider
Style 2 (classic) → Gemini Provider  
Style 3 (vibrant) → SDXL Provider
    ↓
Parallel async generation
    ↓
Upload to S3 with provider metadata
    ↓
Return array with provider labels
```

## Components and Interfaces

### 1. API Gateway Route Configuration

**Current Issue**: The `/signboards/select` endpoint may not be properly configured in template.yaml

**Solution**: Verify API Gateway routes and ensure proper Lambda integration

```yaml
# template.yaml
SignboardSelectApi:
  Type: AWS::Serverless::Api
  Properties:
    StageName: !Ref Environment
    DefinitionBody:
      paths:
        /signboards/select:
          post:
            x-amazon-apigateway-integration:
              type: aws_proxy
              httpMethod: POST
              uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${SignboardAgent.Arn}/invocations
```

### 2. Lambda Handler Action Routing

**Current Issue**: The Lambda handler receives the request but may not properly parse the action from the endpoint path

**Solution**: Update Lambda handler to detect action from either:
- Request body: `body.action = 'select'`
- Request path: `/signboards/select` → infer action='select'

```python
def execute(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    # Parse action from body or path
    body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
    action = body.get('action')
    
    # Infer action from path if not in body
    if not action:
        path = event.get('path', '') or event.get('rawPath', '')
        if '/select' in path:
            action = 'select'
        elif '/generate' in path:
            action = 'generate'
    
    # Route to appropriate handler
    if action == 'select':
        return self._handle_image_selection(...)
```

### 3. Provider Distribution Logic

**Current Issue**: The provider mapping in `_generate_images_async` assigns providers incorrectly

**Current Code**:
```python
provider_mapping = {
    0: "dalle" if "dalle" in prioritized_providers else ...,
    1: "gemini" if "gemini" in prioritized_providers else ...,
    2: "bedrock_sdxl" if "bedrock_sdxl" in prioritized_providers else ...
}
```

**Problem**: The fallback logic causes all images to use the same provider if one is missing

**Solution**: Strict provider assignment with explicit error handling

```python
def _assign_providers_to_styles(self, styles: List[str]) -> List[Tuple[str, str]]:
    """
    Assign providers to styles with strict 1:1 mapping
    
    Returns: List of (provider_name, style) tuples
    """
    # Required provider order
    required_providers = ["dalle", "gemini", "bedrock_sdxl"]
    
    # Check availability
    available_providers = []
    for provider_name in required_providers:
        if provider_name in self.ai_providers:
            available_providers.append(provider_name)
        else:
            self.logger.warning(f"Provider {provider_name} not available")
    
    # Assign providers to styles
    assignments = []
    for i, style in enumerate(styles[:3]):
        if i < len(available_providers):
            provider_name = available_providers[i]
        else:
            # Fallback: reuse available providers
            provider_name = available_providers[i % len(available_providers)]
        
        assignments.append((provider_name, style))
        self.logger.info(f"Assigned {provider_name} to {style} style")
    
    return assignments
```

### 4. English Translation Enhancement

**Current Issue**: Limited translation dictionary and no romanization fallback

**Solution**: Expand translation dictionary and add romanization library

```python
def _translate_to_english(self, korean_name: str) -> str:
    """Enhanced Korean to English translation"""
    
    # Expanded translation dictionary
    translations = {
        # Existing translations...
        '좋은키친': 'Good Kitchen',
        
        # New translations
        '카페': 'Cafe',
        '레스토랑': 'Restaurant',
        '베이커리': 'Bakery',
        '치킨': 'Chicken',
        '피자': 'Pizza',
        '버거': 'Burger',
        '스시': 'Sushi',
        '바': 'Bar',
        '펍': 'Pub',
        '그릴': 'Grill',
        '비스트로': 'Bistro',
        '델리': 'Deli',
        # ... more translations
    }
    
    # Check exact match
    if korean_name in translations:
        return translations[korean_name]
    
    # Check partial matches
    for korean, english in translations.items():
        if korean in korean_name:
            return korean_name.replace(korean, english)
    
    # Fallback: Use romanization
    try:
        from korean_romanizer import romanize
        romanized = romanize(korean_name)
        self.logger.info(f"Romanized {korean_name} → {romanized}")
        return romanized
    except:
        # Last resort: return as-is
        return korean_name
```

### 5. Prompt Enhancement for English Text

**Current Issue**: Prompts don't emphasize English text strongly enough

**Solution**: Restructure prompt to prioritize English text display

```python
def _create_image_prompt(self, business_name: str, business_info: BusinessInfo, style: str) -> str:
    """Enhanced prompt with English text emphasis"""
    
    # Translate to English
    english_name = self._translate_to_english(business_name)
    
    # Log translation
    self.logger.info(f"Business name translation: {business_name} → {english_name}")
    
    # Build prompt with strong English text emphasis
    prompt = (
        f"Professional storefront signboard design. "
        f"Large bold text displaying '{english_name}' in English letters. "
        f"The signboard prominently shows '{english_name}' as the main focal point. "
        f"{style} style, clean typography, business-appropriate design. "
        f"Text: '{english_name}'"
    )
    
    # Validate prompt length (Titan limit: 512 chars)
    if len(prompt) > 512:
        prompt = (
            f"Signboard with '{english_name}' text in bold English letters. "
            f"{style} style, professional design. "
            f"Main text: '{english_name}'"
        )
    
    return prompt
```

## Data Models

### SignboardSelection Request

```python
{
    "sessionId": "string",
    "selectedImageUrl": "string"  # S3 URL of selected image
}
```

### SignboardSelection Response

```python
{
    "sessionId": "string",
    "selectedImageUrl": "string",
    "message": "간판 이미지가 선택되었습니다.",
    "nextStep": "interior",
    "canProceed": true
}
```

### ImageResult with Provider

```python
{
    "url": "s3://...",
    "provider": "dalle" | "gemini" | "bedrock_sdxl",
    "style": "modern" | "classic" | "vibrant",
    "prompt": "string",
    "metadata": {
        "business_name": "string",
        "english_name": "string",  # NEW
        "translation_method": "dictionary" | "romanization",  # NEW
        "is_bedrock": boolean,
        "latency_ms": number
    }
}
```

## Error Handling

### Selection API Errors

1. **Missing sessionId**: Return 400 Bad Request
2. **Missing selectedImageUrl**: Return 400 Bad Request
3. **DynamoDB update failure**: Return 500 Internal Server Error with retry suggestion
4. **Session not found**: Return 404 Not Found

### Provider Distribution Errors

1. **All providers unavailable**: Use fallback images for all 3 styles
2. **One provider fails**: Use fallback for that specific image only
3. **Provider initialization error**: Log error and skip that provider

### Translation Errors

1. **Romanization library missing**: Fall back to simple character mapping
2. **Empty business name**: Use "Business" as default
3. **Translation not found**: Use romanization or original name

## Testing Strategy

### Unit Tests (Not Used - Integration Tests Only)

Per project policy, we use Docker-based integration tests only.

### Integration Tests

1. **Test Selection API**
   - Create session with signboard images
   - Call `/signboards/select` with valid image URL
   - Verify session updated in DynamoDB
   - Verify response contains nextStep='interior'

2. **Test Provider Distribution**
   - Generate 3 signboard images
   - Verify each image has different provider (dalle, gemini, sdxl)
   - Verify provider metadata in S3 objects
   - Check CloudWatch logs for provider assignments

3. **Test English Translation**
   - Generate signboards with Korean business names
   - Verify prompts contain English translations
   - Check S3 metadata for translation info
   - Validate image generation success rate

### Manual Testing

1. **Streamlit UI Flow**
   - Create session → Generate names → Select name
   - Generate signboards → Verify 3 different providers shown
   - Click "이 디자인 선택" → Verify success message
   - Check DynamoDB for selected_image_url

2. **CloudWatch Logs Verification**
   - Check for "Assigned {provider} to {style}" logs
   - Verify "Business name translation: X → Y" logs
   - Monitor Bedrock API call logs

## Performance Considerations

- **Parallel Generation**: All 3 providers generate simultaneously (≤30 seconds total)
- **Provider Timeout**: Each provider has 30-second timeout
- **Selection API**: Should respond in <1 second (DynamoDB update only)
- **Translation**: In-memory dictionary lookup (<1ms)

## Security Considerations

- **API Key Management**: All provider API keys stored in AWS Secrets Manager
- **S3 Access**: Pre-signed URLs with 1-hour expiration
- **Input Validation**: Sanitize business names before translation
- **SQL Injection**: N/A (using DynamoDB, not SQL)

## Deployment Notes

1. Update `template.yaml` to ensure `/signboards/select` route exists
2. Deploy Lambda with updated provider distribution logic
3. Verify all 3 providers (DALL-E, Gemini, SDXL) are initialized
4. Test selection API with curl before UI testing
5. Monitor CloudWatch logs for provider assignments
