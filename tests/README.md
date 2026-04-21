# Backend Test Suite

This directory contains backend validation assets grouped by scope.

## Directory Structure

- `unit/`: isolated behavior tests for individual functions and modules.
- `integration/`: interaction tests across multiple backend components.
- `e2e/`: full workflow tests from input mapping to output validation.
- `system/`: broad validation runners and quality audits.
- `validation/`: dataset, mapping, tariff, and alignment validation checks.
- `analysis/`: exploratory diagnostics and investigation scripts.

## Typical Commands

Run from the backend root:

```bash
pytest tests/unit
pytest tests/integration
python tests/e2e/test_complete_flow.py
python tests/system/run_backend_tests.py
python tests/validation/validate_ui_training_mapping.py
```

## Authoring Guidance

- Unit tests should target one logical behavior per test and avoid heavy external dependencies.
- Integration tests should validate contracts between routers, services, and predictor logic.
- End-to-end tests should cover realistic user payloads and expected response structures.
- Validation scripts should be used to protect feature mapping and dataset consistency.
