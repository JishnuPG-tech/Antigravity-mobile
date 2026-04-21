<p align="center">
	<img src="https://img.shields.io/badge/Python-3.10%2B-3776AB" alt="Python" />
	<img src="https://img.shields.io/badge/FastAPI-0.110-009688" alt="FastAPI" />
	<img src="https://img.shields.io/badge/TensorFlow-2.16-FF6F00" alt="TensorFlow" />
	<img src="https://img.shields.io/badge/Scikit--learn-1.7-F7931E" alt="Scikit-learn" />
	<img src="https://img.shields.io/badge/License-MIT-2E7D32" alt="License" />
</p>

# SmartWatt Backend

SmartWatt Backend is a FastAPI service for appliance-level electricity estimation. It combines trained machine learning models with deterministic physics rules to provide stable and explainable predictions for Kerala household usage patterns.

## Core Capabilities

- Hybrid inference pipeline: model-based inference for complex loads and physics-first calculations for linear loads.
- Batch and single-appliance prediction APIs.
- KSEB slab-aware bill estimation.
- Anomaly diagnostics and confidence metadata.
- Simulation endpoint for what-if savings scenarios.
- Self-learning bias adjustment for recurring users.

## Interface Preview

| API Documentation | Backend Outputs |
|---|---|
| <img src="../docs/screenshots/backend-api-docs.png" alt="Backend API docs" width="100%" /> | <img src="../docs/screenshots/smartwatt-results.png" alt="Backend output sample" width="100%" /> |

If images are not visible yet, add files in `docs/screenshots/` from the repository root.

## Technology Stack

- Python 3.10+
- FastAPI 0.110
- TensorFlow 2.16
- Scikit-learn 1.7
- Pandas and NumPy

## Project Layout

- `main.py`: application bootstrap and base endpoints.
- `routers/appliances.py`: prediction and simulation routes.
- `predictor.py`: model loading, hybrid inference, and confidence logic.
- `physics_engine.py`: deterministic appliance power rules.
- `kseb_tariff.py`: tariff and billing computations.
- `services/`: normalization, batch prediction, load balancing, and learning pipeline.
- `tests/`: unit, integration, e2e, system, and validation suites.

## Local Setup

1. Move to the backend directory.

```bash
cd Backend
```

2. Create and activate a virtual environment.

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies.

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. Start the API server.

```bash
python -m uvicorn main:app --reload --port 8000
```

## API Endpoints

- `GET /`: service status.
- `GET /health`: health probe.
- `POST /calculate-bill`: KSEB bill calculation.
- `POST /predict-appliance`: single appliance prediction.
- `POST /predict-all`: batch prediction across appliances.
- `POST /simulate-savings`: scenario-based optimization insights.

## Runtime Characteristics

- Preloads appliance models during startup for faster first-response behavior.
- Uses schema validation and field mapping before prediction execution.
- Balances modeled appliances with capped system load for realistic totals.
- Supports anomaly flags and confidence metadata in response insights.

## Testing

Run tests from the backend directory.

```bash
pytest tests/unit
pytest tests/integration
python tests/system/run_backend_tests.py
```

## License

Licensed under the MIT License. See `LICENSE`.
