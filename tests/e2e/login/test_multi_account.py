import pytest
import os
import yaml
from typing import List
from playwright.async_api import Page

def load_test_accounts() -> List[dict]:
    """Load multiple test accounts from YAML."""
    # Use environment variables for primary account if available
    primary = {
        "email": os.getenv("MS_REWARDS_E2E_EMAIL"),
        "password": os.getenv("MS_REWARDS_E2E_PASSWORD"),
        "totp_secret": os.getenv("MS_REWARDS_E2E_TOTP_SECRET")
    }
    
    accounts = []
    if primary["email"] and primary["password"]:
        accounts.append(primary)
        
    # Also load from mock_accounts.yaml if it exists
    mock_path = "tests/e2e/data/mock_accounts.yaml"
    if os.path.exists(mock_path):
        try:
            with open(mock_path) as f:
                data = yaml.safe_load(f)
            file_accounts = data.get("test_accounts", [])
            for acc in file_accounts:
                # Basic substitution for environment variables in the file
                email = acc.get("email", "")
                if "${MS_REWARDS_E2E_EMAIL}" in email:
                    email = email.replace("${MS_REWARDS_E2E_EMAIL}", os.getenv("MS_REWARDS_E2E_EMAIL", ""))
                
                password = acc.get("password", "")
                if "${MS_REWARDS_E2E_PASSWORD}" in password:
                    password = password.replace("${MS_REWARDS_E2E_PASSWORD}", os.getenv("MS_REWARDS_E2E_PASSWORD", ""))
                
                if email and password and email != primary["email"]:
                     accounts.append({
                         "email": email,
                         "password": password,
                         "totp_secret": acc.get("totp_secret")
                     })
        except:
            pass
            
    return accounts

@pytest.mark.e2e
@pytest.mark.requires_login
@pytest.mark.parametrize("account", load_test_accounts(), ids=lambda acc: acc.get("email", "unknown"))
async def test_login_with_multiple_accounts(page: Page, account):
    """Test login works across multiple configured test accounts."""
    if not account.get("email") or not account.get("password"):
        pytest.skip("Account missing email or password")
        
    from tests.e2e.helpers.login import perform_login
    await perform_login(page, account)
    assert "rewards.bing.com" in page.url
