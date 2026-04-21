import os
import shutil
import sys
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Add parent to path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Import the module to be tested
from train import train_appliance_model


# Helper to create dummy dataframe matching  schema
def create_dummy_data():
    data = {
        "total_kwh_monthly": [500] * 110,
        "n_occupants": [4] * 110,
        "location_type": ["urban"] * 110,
        # AC Data
        "has_test_ac": [1] * 110,
        "ac_hours_per_day": [8] * 110,
        "ac_tonnage": [1.5] * 110,
        "ac_star_rating": [3] * 110,
        "ac_type": ["split"] * 110,
        # Targets
        "test_ac_real_efficiency_factor": [1.0] * 110,
        "test_ac_real_effective_hours": [8.0] * 110,
    }
    return pd.DataFrame(data)


def test__training_logic():
    """Verify that train_appliance_model runs  Multi-Output logic"""

    # 1. Setup Data
    df = create_dummy_data()

    # 2. Setup Test output directory
    test_models_dir = "models"
    if not os.path.exists(test_models_dir):
        os.makedirs(test_models_dir)

    # 3. Mock Model Saving and Fitting to avoid heaviness
    with patch("train.build_multi_output_model") as mock_build, patch(
        "train.joblib.dump"
    ) as mock_joblib:

        # Return a Mock Keras Model
        mock_model = MagicMock()
        mock_build.return_value = mock_model
        # Mock evaluate return specific metrics (efficiency_mae, hours_mae)
        # model.evaluate returns list usually: [loss, loss_eff, loss_hours, mae_eff, mae_hours]
        mock_model.evaluate.return_value = [0.1, 0.05, 0.05, 0.01, 0.2]

        # Run Function
        train_appliance_model(
            df=df,
            app_name="test_ac",
            target_cols=[
                "test_ac_real_efficiency_factor",
                "test_ac_real_effective_hours",
            ],
            features=[
                "n_occupants",
                "total_kwh_monthly",
                "ac_tonnage",
                "ac_star_rating",
                "ac_type",
            ],
        )

        # Assertions
        assert mock_build.called, "Should build multi-output model"
        assert mock_model.fit.called, "Should call model.fit"
        assert mock_model.save.called, "Should save keras model"
        assert mock_joblib.called, "Should save preprocessor"

        # Verify save path
        save_args = mock_model.save.call_args[0][0]
        assert "models/test_ac_model.keras" in save_args


def test_insufficient_data_skip():
    """Verify training is skipped if data samples < 100"""
    df = create_dummy_data().head(50)  # only 50 samples (threshold is 100 in )

    with patch("train.build_multi_output_model") as mock_build:
        train_appliance_model(
            df=df,
            app_name="test_ac",
            target_cols=["eff", "hours"],
            features=["n_occupants"],
        )
        assert (
            not mock_build.called
        ), "Should skip training for insufficient data (<100)"


if __name__ == "__main__":
    pytest.main([__file__])
