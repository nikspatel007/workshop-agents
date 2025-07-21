# How to Run Tests for BS Detector

## Important: Python Environment Issues

If you're seeing test failures about missing modules even though `verify_setup.py` shows everything is installed, you likely have pytest installed via pipx or in a different environment.

## Solution 1: Install pytest in your current environment

```bash
pip3 install pytest
```

Then run tests with:
```bash
python3 -m pytest bs_detector/tests/ -v
```

## Solution 2: Use the verify script

If you just want to verify your setup without pytest:
```bash
python3 verify_setup.py
```

## Solution 3: Run tests from within Python

```python
# From the workshop-agents directory
import subprocess
import sys

result = subprocess.run([sys.executable, "-m", "pytest", "bs_detector/tests/", "-v"])
```

## Expected Test Results

When everything is working correctly:
- ✅ test_tool_registry 
- ✅ test_tool_not_found
- ✅ test_mock_search
- ✅ test_detect_environment
- ✅ test_get_settings
- ✅ test_platform_detection
- ✅ test_factory_creates_openai_llm (if langchain-openai installed)
- ✅ test_factory_raises_for_unknown_provider
- ✅ test_factory_raises_for_missing_api_key (if langchain-openai installed)
- ✅ test_factory_temperature_parameter (if langchain-openai installed)

## Common Issues

1. **"No module named 'langchain'"**: The packages are installed in a different Python environment. Use `python3 -m pytest` instead of just `pytest`.

2. **"No module named 'pytest'"**: Install pytest in your current environment with `pip3 install pytest`.

3. **Import errors**: Make sure you're running from the `workshop-agents` directory, not from inside `bs_detector/`.