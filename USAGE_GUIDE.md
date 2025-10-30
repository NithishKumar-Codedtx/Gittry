# Test Case Priority Analysis - Usage Guide

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create/update `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
GITHUB_TOKEN=your_github_token_here
```

Get your OpenAI API key from: https://platform.openai.com/api-keys

## Running the Analysis

### Basic Usage
```bash
python run_analysis.py
```

### How It Works

The system analyzes Git commits and intelligently identifies which test cases need to be run based on the changed files.

**Matching Rules:**

1. **Homepage files** (index.html, home.jsx, home.css) → Returns "Homepage" module tests
2. **Contact files** (contact.jsx, contact-form.html) → Returns "Contact Form" module tests
3. **API/Backend files** (server.js, routes/, api/) → Returns "API Routes" module tests
4. **Performance files** (webpack.config, package.json) → Returns "Performance" module tests
5. **Global files** (global.css, app.css) → Returns ALL module tests
6. **Test/Sample files** (sample.py, test.py) → Ignored (returns empty list)

### Example Outputs

#### Scenario 1: Homepage Change
```
Changed files: index.html, home.css
Result: TC_HP_001, TC_HP_002, TC_HP_003 (Homepage tests)
```

#### Scenario 2: Contact Form Change
```
Changed files: contact.jsx
Result: TC_CF_001, TC_CF_002, TC_CF_003 (Contact Form tests)
```

#### Scenario 3: Multiple Modules
```
Changed files: index.html, contact.jsx, server.js
Result: Homepage, Contact Form, and API Routes tests
```

#### Scenario 4: Sample/Test Files
```
Changed files: Sample.py, test.js
Result: [] (empty - no tests needed)
```

## Configuration

### Change Commit ID
Edit `run_analysis.py` line 13:
```python
COMMIT_ID = "your_commit_hash_here"
```

### Change Repository
Edit `run_analysis.py` line 14:
```python
GITHUB_REPO = "username/repository"
```

### Test Mode
If GitHub API fails, the system automatically falls back to test mode with example files.

## Customization

### Add New Modules
Update the matching rules in `run_analysis.py` around line 145:

```python
8. **Your New Module** → "New Module" name
   - new-page.html, NewComponent.jsx
   - ANY file in folders: /newmodule
   - Return test cases where Module = "New Module"
```

### Adjust AI Model
Change line 24 in `run_analysis.py`:
```python
llm = ChatOpenAI(
    model="gpt-4o-mini",  # or "gpt-4", "gpt-4-turbo"
    temperature=0,
)
```

## Webhook Integration

To run this automatically on every commit, use `webhook_listener.py`:

```bash
python webhook_listener.py
```

Then configure GitHub webhook to POST to: `http://your-server:5000/webhook`

## Troubleshooting

### Issue: Returns empty list []
**Causes:**
- Changed files don't match any module (e.g., README.md, Sample.py)
- This is correct behavior - not all files need testing

### Issue: Returns ALL test cases
**Possible Causes:**
- Changed file is global (e.g., global.css, app.js)
- AI is being too generous with matching

**Solution:** Update matching rules to be more specific

### Issue: GitHub API authentication fails
**Solutions:**
1. Check your GITHUB_TOKEN in .env file
2. Verify token has repo access permissions
3. System will fall back to test mode automatically

### Issue: OpenAI API errors
**Solutions:**
1. Check OPENAI_API_KEY in .env file
2. Verify you have API credits
3. Check rate limits

## Output Format

The system provides:
1. **List of changed files**
2. **AI analysis process** (verbose mode)
3. **Selected test case IDs**
4. **Summary by module**

Example output:
```
==================================================
SELECTED TEST CASES TO RUN
==================================================
  - TC_HP_001
  - TC_HP_002
  - TC_CF_001
==================================================

==================================================
ANALYSIS SUMMARY
==================================================
Total selected test cases: 3
Affected modules:
  - Homepage: 2 test(s)
  - Contact Form: 1 test(s)
==================================================
```

## Best Practices

1. **Commit IDs:** Use full commit hashes, not short ones
2. **Module Names:** Keep module names consistent in your test case Excel file
3. **File Organization:** Organize your code by module for better matching
4. **Testing:** Test with different commit scenarios before production use

## Support

For issues or questions:
1. Check this guide first
2. Review the console output for error messages
3. Test with example files in test mode
4. Check OpenAI and GitHub API status
