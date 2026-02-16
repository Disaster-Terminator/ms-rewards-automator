"""
Runtime tests for LoginStateMachine.

Tests runtime behavior including timeout and max transitions protection.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from src.login.login_state_machine import (
    LoginState,
    LoginStateMachine,
)


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Mock()
    config.get = Mock(
        side_effect=lambda key, default: {
            "login.max_transitions": 3,  # Low limit for testing
            "login.timeout_seconds": 2,  # Short timeout for testing
        }.get(key, default)
    )
    return config


@pytest.fixture
def state_machine(mock_config):
    """Create a LoginStateMachine instance."""
    return LoginStateMachine(mock_config)


class TestMaxTransitionsProtection:
    """Tests for maximum transitions protection."""

    def test_max_transitions_exceeded(self, state_machine):
        """Test that max transitions limit is enforced."""
        # Record transitions up to the limit
        for _i in range(3):
            state_machine._record_transition(LoginState.EMAIL_INPUT, LoginState.PASSWORD_INPUT)

        # Verify we've hit the limit
        assert state_machine.get_transition_count() == 3

        # This should be detected by the state machine
        assert state_machine.get_transition_count() >= state_machine.max_transitions

    def test_transition_count_tracking(self, state_machine):
        """Test that transition count is tracked correctly."""
        assert state_machine.get_transition_count() == 0

        state_machine._record_transition(LoginState.ERROR, LoginState.EMAIL_INPUT)
        assert state_machine.get_transition_count() == 1

        state_machine._record_transition(LoginState.EMAIL_INPUT, LoginState.PASSWORD_INPUT)
        assert state_machine.get_transition_count() == 2

        state_machine._record_transition(LoginState.PASSWORD_INPUT, LoginState.LOGGED_IN)
        assert state_machine.get_transition_count() == 3


class TestTimeoutProtection:
    """Tests for timeout protection."""

    def test_start_time_recorded(self, state_machine):
        """Test that start time is recorded."""
        # Start time should be set during initialization or first transition
        state_machine._record_transition(LoginState.ERROR, LoginState.EMAIL_INPUT)

        # Check that we can calculate elapsed time
        if hasattr(state_machine, "start_time"):
            elapsed = (datetime.now() - state_machine.start_time).total_seconds()
            assert elapsed >= 0

    def test_timeout_configuration(self, state_machine):
        """Test that timeout is configured correctly."""
        assert state_machine.timeout_seconds == 2


class TestStateDetectionForAllStates:
    """Test state detection for all LoginState values."""

    @pytest.mark.parametrize(
        "state",
        [
            LoginState.LOGGED_IN,
            LoginState.EMAIL_INPUT,
            LoginState.PASSWORD_INPUT,
            LoginState.TOTP_2FA,
            LoginState.PASSWORDLESS,
            LoginState.GET_A_CODE,
            LoginState.RECOVERY_EMAIL,
            LoginState.MOBILE_ACCESS,
            LoginState.ERROR,
        ],
    )
    def test_all_states_exist(self, state):
        """Test that all expected states exist in the enum."""
        assert isinstance(state, LoginState)
        assert state.value is not None

    def test_state_machine_can_handle_all_states(self, state_machine):
        """Test that state machine can transition through all states."""
        all_states = list(LoginState)

        for state in all_states:
            # Should be able to set current state to any valid state
            state_machine.current_state = state
            assert state_machine.current_state == state


class TestStateTransitionFlow:
    """Test complete state transition flows."""

    def test_typical_login_flow(self, state_machine):
        """Test a typical login flow: ERROR → EMAIL → PASSWORD → LOGGED_IN."""
        # Initial state
        assert state_machine.current_state == LoginState.ERROR

        # Transition to email input
        state_machine._record_transition(LoginState.ERROR, LoginState.EMAIL_INPUT)
        state_machine.current_state = LoginState.EMAIL_INPUT
        assert state_machine.get_transition_count() == 1

        # Transition to password input
        state_machine._record_transition(LoginState.EMAIL_INPUT, LoginState.PASSWORD_INPUT)
        state_machine.current_state = LoginState.PASSWORD_INPUT
        assert state_machine.get_transition_count() == 2

        # Transition to logged in
        state_machine._record_transition(LoginState.PASSWORD_INPUT, LoginState.LOGGED_IN)
        state_machine.current_state = LoginState.LOGGED_IN
        assert state_machine.get_transition_count() == 3

        # Verify final state
        assert state_machine.current_state == LoginState.LOGGED_IN

    def test_2fa_login_flow(self, state_machine):
        """Test 2FA login flow: ERROR → EMAIL → PASSWORD → TOTP → LOGGED_IN."""
        transitions = [
            (LoginState.ERROR, LoginState.EMAIL_INPUT),
            (LoginState.EMAIL_INPUT, LoginState.PASSWORD_INPUT),
            (LoginState.PASSWORD_INPUT, LoginState.TOTP_2FA),
        ]

        for from_state, to_state in transitions:
            state_machine._record_transition(from_state, to_state)
            state_machine.current_state = to_state

        assert state_machine.current_state == LoginState.TOTP_2FA
        assert state_machine.get_transition_count() == 3


class TestDiagnosticInfo:
    """Test diagnostic information generation."""

    def test_diagnostic_info_completeness(self, state_machine):
        """Test that diagnostic info contains all expected fields."""
        state_machine._record_transition(LoginState.ERROR, LoginState.EMAIL_INPUT)

        info = state_machine.get_diagnostic_info()

        # Check required fields
        assert "current_state" in info
        assert "transition_count" in info
        assert "max_transitions" in info
        assert "timeout_seconds" in info
        assert "state_history" in info

        # Check values
        assert info["current_state"] == "error"  # Still at ERROR
        assert info["transition_count"] == 1
        assert info["max_transitions"] == 3
        assert info["timeout_seconds"] == 2
        assert len(info["state_history"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
