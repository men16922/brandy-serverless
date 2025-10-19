# Requirements Document

## Introduction

This document outlines the requirements for fixing three critical issues in the signboard generation system:
1. Signboard selection failure when clicking selection button
2. All images using SDXL provider instead of distributing across DALL-E, Gemini, and SDXL
3. Signboard text not displaying in English as intended

## Requirements

### Requirement 1: Fix Signboard Selection API

**User Story:** As a user, I want to select a signboard design by clicking the selection button, so that I can proceed to the interior design step.

#### Acceptance Criteria

1. WHEN user clicks "이 디자인 선택" button THEN the system SHALL successfully save the selected image URL to the session
2. WHEN the selection API is called THEN the system SHALL return HTTP 200 with success message
3. WHEN selection succeeds THEN the system SHALL update currentStep to 4 (interior step)
4. IF the API endpoint `/signboards/select` is called THEN the Lambda SHALL handle it with action='select'
5. WHEN selection fails THEN the system SHALL display a clear error message to the user

### Requirement 2: Distribute Image Generation Across Multiple Providers

**User Story:** As a user, I want to see signboard designs from different AI providers (DALL-E, Gemini, SDXL), so that I can compare different artistic styles and choose the best one.

#### Acceptance Criteria

1. WHEN generating 3 signboard images THEN the system SHALL use exactly one image from each provider: DALL-E, Gemini, and SDXL
2. WHEN assigning providers to styles THEN the system SHALL map:
   - Style 1 (modern) → DALL-E
   - Style 2 (classic) → Gemini  
   - Style 3 (vibrant) → SDXL
3. WHEN displaying images THEN each image SHALL show its provider name (DALLE, GEMINI, SDXL) in the UI
4. IF a provider fails THEN the system SHALL use fallback image for that specific provider only
5. WHEN all 3 images are generated THEN the system SHALL log which provider was used for each style

### Requirement 3: Display Signboard Text in English Only

**User Story:** As a user, I want signboard designs to display business names in English letters, so that the text is clearly readable and professionally rendered by AI image generators.

#### Acceptance Criteria

1. WHEN generating image prompts THEN the system SHALL convert Korean business names to English
2. WHEN the business name is in Korean THEN the system SHALL use the translation mapping or transliteration
3. WHEN the prompt is created THEN the system SHALL emphasize "text in large bold English letters" in the prompt
4. WHEN the prompt includes the business name THEN it SHALL appear at least twice in the prompt for emphasis
5. IF the business name contains Korean characters THEN the system SHALL NOT pass them directly to the image generator

### Requirement 4: Improve English Translation Quality

**User Story:** As a developer, I want better Korean-to-English translation for business names, so that signboard text looks professional and meaningful.

#### Acceptance Criteria

1. WHEN translating common Korean words THEN the system SHALL use the expanded translation dictionary
2. WHEN the business name contains "카페" THEN it SHALL be translated to "Cafe"
3. WHEN the business name contains "레스토랑" THEN it SHALL be translated to "Restaurant"
4. WHEN no direct translation exists THEN the system SHALL use romanization as fallback
5. WHEN translation is applied THEN the system SHALL log the original and translated names for debugging
