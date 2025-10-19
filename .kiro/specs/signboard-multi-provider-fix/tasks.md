# Implementation Plan

- [x] 1. Fix signboard selection API routing
  - Update Lambda handler to detect action from request path
  - Ensure `/signboards/select` endpoint properly routes to `_handle_image_selection`
  - Add logging for action detection and routing
  - _Requirements: 1.1, 1.2, 1.4_

- [ ] 2. Implement strict provider-to-style assignment
- [x] 2.1 Create `_assign_providers_to_styles` method
  - Write method that returns List of (provider_name, style) tuples
  - Implement strict 1:1 mapping: DALL-E→modern, Gemini→classic, SDXL→vibrant
  - Add availability checking for each required provider
  - Log provider assignments for debugging
  - _Requirements: 2.1, 2.2, 2.5_

- [x] 2.2 Update `_generate_images_async` to use new assignment logic
  - Replace existing provider_mapping dictionary with `_assign_providers_to_styles` call
  - Update task creation loop to use assigned (provider, style) tuples
  - Remove fallback logic that causes all images to use same provider
  - Ensure each style gets exactly one provider
  - _Requirements: 2.1, 2.2_

- [x] 2.3 Add provider metadata to image results
  - Update `_image_result_to_dict` to include provider name prominently
  - Ensure Streamlit UI displays provider labels (DALLE, GEMINI, SDXL)
  - Add provider info to S3 object metadata
  - _Requirements: 2.3_

- [ ] 3. Enhance English translation for business names
- [x] 3.1 Expand translation dictionary
  - Add common Korean food/business terms (카페, 레스토랑, 베이커리, etc.)
  - Add romanization fallback using simple character mapping
  - Log original and translated names for debugging
  - _Requirements: 3.2, 4.1, 4.2, 4.3, 4.5_

- [x] 3.2 Update `_create_image_prompt` for English emphasis
  - Call `_translate_to_english` at start of method
  - Restructure prompt to repeat English name multiple times
  - Add "text in large bold English letters" emphasis
  - Ensure prompt stays under 512 character limit
  - _Requirements: 3.1, 3.3, 3.4_

- [x] 3.3 Add translation metadata to image results
  - Store english_name in metadata
  - Store translation_method (dictionary/romanization)
  - Log translation for debugging
  - _Requirements: 3.5, 4.5_

- [x] 4. Verify API Gateway configuration
  - Check template.yaml for `/signboards/select` route
  - Ensure Lambda integration is properly configured
  - Test endpoint with curl before UI testing
  - _Requirements: 1.1, 1.2_

- [x] 5. Update error handling and logging
  - Add specific error messages for selection failures
  - Log provider assignments in CloudWatch
  - Log translation results for debugging
  - Add error recovery for missing providers
  - _Requirements: 1.5, 2.4, 2.5_

- [x] 6. Integration testing
  - Test selection API with real session data
  - Verify 3 different providers are used for 3 images
  - Check English text appears in generated images
  - Validate CloudWatch logs show correct provider assignments
  - _Requirements: All_
