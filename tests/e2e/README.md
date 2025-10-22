# End-to-End Testing for Streamlit Workflow

## Overview

This directory contains automated end-to-end tests for the AI Branding Chatbot Streamlit application.

## Test Types

### 1. API-Based Testing (`test_streamlit_workflow.py`)
Tests the complete workflow by directly calling AWS API endpoints.

**Advantages:**
- ✅ Fast execution (no UI rendering)
- ✅ Easy to run in CI/CD
- ✅ Tests backend logic directly
- ✅ No browser dependencies

**What it tests:**
- Session creation
- Business analysis
- Name generation (async)
- Signboard generation (async)
- Interior recommendations (async)
- Report generation

### 2. UI-Based Testing (`test_streamlit_ui.py`)
Tests the actual Streamlit UI using Playwright.

**Advantages:**
- ✅ Tests real user interactions
- ✅ Validates UI elements
- ✅ Catches UI bugs
- ✅ Screenshots on failure

**What it tests:**
- Form filling (country, city, industry, size)
- Button clicks
- Navigation between steps
- Async polling UI feedback
- Report download

---

## Prerequisites

### For API Testing

```bash
# Install dependencies
pip install requests

# Ensure AWS API is deployed
sam deploy --config-env dev
```

### For UI Testing

```bash
# Install Playwright
pip install playwright pytest-playwright

# Install browsers
playwright install chromium

# Start Streamlit app
streamlit run src/streamlit/app.py
```

---

## Running Tests

### 1. API-Based Test

```bash
# Run from project root
python tests/e2e/test_streamlit_workflow.py
```

**Expected output:**
```
================================================================================
Starting Full Workflow Test
================================================================================

================================================================================
STEP 1: Business Analysis
================================================================================
Creating session...
✅ Session created: abc-123-def-456
Starting business analysis...
✅ Analysis complete!
   Score: 85
   Summary: Strong market potential for Korean fusion restaurant...

================================================================================
STEP 2: Business Name Generation
================================================================================
Starting name generation (async)...
✅ Name generation started, polling for results...
   Polling... (30s elapsed)
✅ Name generation complete! (3 names)
   1. Seoul Fusion (score: 0.92)
   2. Hanbok Kitchen (score: 0.88)
   3. K-Town Table (score: 0.85)
✅ Selected name: Seoul Fusion

================================================================================
STEP 3: Signboard Design Generation
================================================================================
Starting signboard generation (async)...
✅ Signboard generation started, polling for results...
   Polling... (60s elapsed)
✅ Signboard generation complete! (3 images)
   1. Style: modern, Provider: bedrock_sdxl
   2. Style: classic, Provider: bedrock_sdxl
   3. Style: vibrant, Provider: dalle
✅ Selected signboard: s3://...
✅ Signboard selected successfully

================================================================================
STEP 4: Interior Recommendations Generation
================================================================================
Starting interior generation (async)...
✅ Interior generation started, polling for results...
   Polling... (30s elapsed)
✅ Interior generation complete! (3 recommendations)
   1. Style: modern
   2. Style: traditional
   3. Style: minimalist

================================================================================
STEP 5: Final Report Generation
================================================================================
Starting report generation...
✅ Report generation complete!
   Report URL: s3://...

================================================================================
✅ ALL TESTS PASSED!
================================================================================

================================================================================
📊 FINAL SESSION SUMMARY
================================================================================
Session ID: abc-123-def-456
Business Name: Seoul Fusion
Current Step: 5
Status: completed
================================================================================
```

### 2. UI-Based Test

```bash
# Ensure Streamlit is running
streamlit run src/streamlit/app.py

# In another terminal, run UI test
python tests/e2e/test_streamlit_ui.py
```

**Expected behavior:**
- Browser window opens automatically
- Form fields are filled automatically
- Buttons are clicked automatically
- Progress through all 5 steps
- Browser closes on completion

**On failure:**
- Screenshot saved as `test_failure.png`
- Check screenshot for UI state

---

## Test Configuration

### API Test Configuration

Edit `test_streamlit_workflow.py`:

```python
# Change API endpoint
API_BASE_URL = "https://your-api-url.execute-api.us-west-2.amazonaws.com/dev"

# Change business info
self.business_info = {
    "industry": "retail",  # Change industry
    "country": "South Korea",  # Change country
    "city": "Seoul",  # Change city
    "size": "medium"  # Change size
}
```

### UI Test Configuration

Edit `test_streamlit_ui.py`:

```python
# Change Streamlit URL
STREAMLIT_URL = "http://localhost:8502"  # Different port

# Run in headless mode (for CI/CD)
browser = p.chromium.launch(headless=True)
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  api-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install requests
      
      - name: Run API tests
        run: python tests/e2e/test_streamlit_workflow.py
        env:
          API_BASE_URL: ${{ secrets.API_BASE_URL }}
  
  ui-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install playwright pytest-playwright
          playwright install chromium
      
      - name: Start Streamlit
        run: |
          streamlit run src/streamlit/app.py &
          sleep 10
      
      - name: Run UI tests
        run: python tests/e2e/test_streamlit_ui.py
      
      - name: Upload screenshots on failure
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-screenshots
          path: test_failure.png
```

---

## Troubleshooting

### API Test Issues

**Problem:** Connection refused
```
❌ Cannot connect to API server
```

**Solution:**
1. Check API endpoint is correct
2. Verify AWS deployment: `sam deploy --config-env dev`
3. Test endpoint manually: `curl https://your-api-url/`

**Problem:** Timeout during polling
```
❌ Name generation timeout
```

**Solution:**
1. Check CloudWatch logs for Lambda errors
2. Increase `max_attempts` in test
3. Verify Lambda timeout settings (should be 180s)

### UI Test Issues

**Problem:** Streamlit not found
```
❌ Navigation timeout
```

**Solution:**
1. Ensure Streamlit is running: `streamlit run src/streamlit/app.py`
2. Check correct port (default: 8501)
3. Wait for Streamlit to fully start (10-15 seconds)

**Problem:** Element not found
```
❌ Selector not found
```

**Solution:**
1. Check screenshot: `test_failure.png`
2. Update selectors in test code
3. Add `time.sleep()` for dynamic content

**Problem:** Browser doesn't close
```
Browser window remains open
```

**Solution:**
1. Check for exceptions in test
2. Ensure `browser.close()` in `finally` block
3. Kill manually: `pkill chromium`

---

## Best Practices

### 1. Run API Tests First
- Faster feedback
- Isolates backend issues
- No UI dependencies

### 2. Use UI Tests for Critical Paths
- User registration
- Payment flows
- Complex interactions

### 3. Add Waits for Async Operations
```python
# Bad
button.click()
next_element.click()  # May fail if async

# Good
button.click()
page.wait_for_selector('text=Success')
next_element.click()
```

### 4. Take Screenshots on Failure
```python
try:
    # Test code
except Exception as e:
    page.screenshot(path=f"failure_{step}.png")
    raise
```

### 5. Clean Up Test Data
```python
# Delete test sessions after test
requests.delete(f"{API_BASE_URL}/sessions/{session_id}")
```

---

## Future Improvements

### 1. Parallel Testing
- Run multiple workflows simultaneously
- Test different business types
- Stress test async polling

### 2. Visual Regression Testing
- Compare screenshots across runs
- Detect UI changes
- Use tools like Percy or Applitools

### 3. Performance Testing
- Measure response times
- Track polling duration
- Monitor resource usage

### 4. Data-Driven Testing
- Test with multiple datasets
- CSV/JSON test data files
- Parameterized tests

### 5. Integration with Monitoring
- Send test results to CloudWatch
- Alert on test failures
- Track test metrics over time

---

## Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Streamlit Testing Guide](https://docs.streamlit.io/library/advanced-features/testing)
- [AWS API Gateway Testing](https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-test-method.html)
- [pytest Documentation](https://docs.pytest.org/)
