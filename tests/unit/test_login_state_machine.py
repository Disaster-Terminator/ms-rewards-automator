"""
Unit tests for LoginStateMachine.

Tests the core functionality of the login state machine including:
- State enumeration
- State transition tracking
- Timeout and max transitions protection
- Handler registration
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from src.login.login_state_machine import (
    LoginState,
    LoginStateMachine,
    StateTransition
)


class TestLoginState:
    """Tests for LoginState enum."""
    
    def test_login_state_values(self):
        """Test that all expected login states exist."""
        expected_states = {
            "logged_in",
            "email_input",
            "password_input",
            "totp_2fa",
            "passwordless",
            "get_a_code",
            "recovery_email",
            "mobile_access",
            "error",
            "otp_code_entry",
            "stay_signed_in",
            "auth_blocked"
        }
        
        actual_states = {state.value for state in LoginState}
        assert actual_states == expected_states
    
    def test_login_state_string_representation(self):
        """Test that LoginState converts to string correctly."""
        assert str(LoginState.EMAIL_INPUT) == "email_input"
        assert str(LoginState.LOGGED_IN) == "logged_in"


class TestStateTransition:
    """Tests for StateTransition class."""
    
    def test_state_transition_creation(self):
        """Test creating a state transition."""
        now = datetime.now()
        transition = StateTransition(
            from_state=LoginState.EMAIL_INPUT,
            to_state=LoginState.PASSWORD_INPUT,
            timestamp=now,
            success=True
        )
        
        assert transition.from_state == LoginState.EMAIL_INPUT
        assert transition.to_state == LoginState.PASSWORD_INPUT
        assert transition.timestamp == now
        assert transition.success is True
        assert transition.error_message is None
    
    def test_state_transition_with_error(self):
        """Test creating a failed state transition."""
        transition = StateTransition(
            from_state=LoginState.EMAIL_INPUT,
            to_state=LoginState.ERROR,
            timestamp=datetime.now(),
            success=False,
            error_message="Test error"
        )
        
        assert transition.success is False
        assert transition.error_message == "Test error"
    
    def test_state_transition_repr(self):
        """Test string representation of state transition."""
        transition = StateTransition(
            from_state=LoginState.EMAIL_INPUT,
            to_state=LoginState.PASSWORD_INPUT,
            timestamp=datetime.now(),
            success=True
        )
        
        repr_str = repr(transition)
        assert "✓" in repr_str
        assert "email_input" in repr_str
        assert "password_input" in repr_str


class TestLoginStateMachine:
    """Tests for LoginStateMachine class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock()
        config.get = Mock(side_effect=lambda key, default: {
            "login.max_transitions": 10,
            "login.timeout_seconds": 300
        }.get(key, default))
        return config
    
    @pytest.fixture
    def state_machine(self, mock_config):
        """Create a LoginStateMachine instance."""
        return LoginStateMachine(mock_config)
    
    def test_initialization(self, state_machine):
        """Test state machine initialization."""
        assert state_machine.current_state == LoginState.ERROR
        assert len(state_machine.state_history) == 0
        assert state_machine.max_transitions == 10
        assert state_machine.timeout_seconds == 300
    
    def test_register_handler(self, state_machine):
        """Test registering a state handler."""
        mock_handler = Mock()
        state_machine.register_handler(LoginState.EMAIL_INPUT, mock_handler)
        
        assert LoginState.EMAIL_INPUT in state_machine.handlers
        assert state_machine.handlers[LoginState.EMAIL_INPUT] == mock_handler
    
    def test_record_transition(self, state_machine):
        """Test recording state transitions."""
        state_machine._record_transition(
            LoginState.EMAIL_INPUT,
            LoginState.PASSWORD_INPUT
        )
        
        assert len(state_machine.state_history) == 1
        transition = state_machine.state_history[0]
        assert transition.from_state == LoginState.EMAIL_INPUT
        assert transition.to_state == LoginState.PASSWORD_INPUT
        assert transition.success is True
    
    def test_get_transition_count(self, state_machine):
        """Test getting transition count."""
        assert state_machine.get_transition_count() == 0
        
        state_machine._record_transition(
            LoginState.EMAIL_INPUT,
            LoginState.PASSWORD_INPUT
        )
        assert state_machine.get_transition_count() == 1
    
    def test_reset(self, state_machine):
        """Test resetting the state machine."""
        state_machine.current_state = LoginState.EMAIL_INPUT
        state_machine._record_transition(
            LoginState.ERROR,
            LoginState.EMAIL_INPUT
        )
        
        state_machine.reset()
        
        assert state_machine.current_state == LoginState.ERROR
        assert len(state_machine.state_history) == 0
    
    def test_get_diagnostic_info(self, state_machine):
        """Test getting diagnostic information."""
        state_machine.current_state = LoginState.EMAIL_INPUT
        state_machine._record_transition(
            LoginState.ERROR,
            LoginState.EMAIL_INPUT
        )
        
        info = state_machine.get_diagnostic_info()
        
        assert info["current_state"] == "email_input"
        assert info["transition_count"] == 1
        assert info["max_transitions"] == 10
        assert info["timeout_seconds"] == 300
        assert len(info["state_history"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
