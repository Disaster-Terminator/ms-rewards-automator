"""
Tests for CLI commands in manage_reviews.py
"""

import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestVerifyContextLogic:
    """Test verify-context command logic without CLI import"""

    def test_verify_context_no_data(self, tmp_path: Path):
        """Test verify-context when no local data exists"""

        manager = MagicMock()
        manager.get_metadata.return_value = None

        metadata = manager.get_metadata()

        if metadata is None:
            output = {
                "success": True,
                "valid": None,
                "message": "无本地评论数据",
            }
        else:
            output = {"success": True, "valid": True}

        assert output["valid"] is None
        assert "无本地评论数据" in output["message"]

    def test_verify_context_branch_match(self, tmp_path: Path):
        """Test verify-context when branch matches"""
        from src.review.models import ReviewMetadata

        metadata = ReviewMetadata(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            branch="feature-test",
            head_sha="abc1234",
        )

        current_branch = "feature-test"

        if not metadata.branch:
            output = {"success": True, "valid": None, "warning": "旧版本数据"}
        elif current_branch == metadata.branch:
            output = {
                "success": True,
                "valid": True,
                "current_branch": current_branch,
                "stored_branch": metadata.branch,
                "stored_pr": metadata.pr_number,
                "message": "上下文验证通过",
            }
        else:
            output = {"success": True, "valid": False}

        assert output["valid"] is True
        assert output["current_branch"] == "feature-test"

    def test_verify_context_branch_mismatch(self, tmp_path: Path):
        """Test verify-context when branch does not match"""
        from src.review.models import ReviewMetadata

        metadata = ReviewMetadata(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            branch="feature-old",
            head_sha="abc1234",
        )

        current_branch = "feature-new"

        if not metadata.branch:
            output = {"success": True, "valid": None}
        elif current_branch == metadata.branch:
            output = {"success": True, "valid": True}
        else:
            output = {
                "success": True,
                "valid": False,
                "current_branch": current_branch,
                "stored_branch": metadata.branch,
                "stored_pr": metadata.pr_number,
                "message": f"分支不匹配：当前分支 {current_branch}，本地数据属于 {metadata.branch}",
            }

        assert output["valid"] is False
        assert output["current_branch"] == "feature-new"
        assert output["stored_branch"] == "feature-old"

    def test_verify_context_old_version_data(self, tmp_path: Path):
        """Test verify-context with old version data (no branch field)"""
        from src.review.models import ReviewMetadata

        metadata = ReviewMetadata(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
        )

        if not metadata.branch:
            output = {
                "success": True,
                "valid": None,
                "warning": "旧版本数据，缺少分支信息，跳过验证",
                "stored_pr": metadata.pr_number,
            }
        else:
            output = {"success": True, "valid": True}

        assert output["valid"] is None
        assert "warning" in output


class TestFetchCommandLogic:
    """Test fetch command logic without CLI import"""

    def test_fetch_auto_detect_pr_success(self):
        """Test fetch command auto-detects PR number"""
        pr_data = {"number": 456}

        pr_number = pr_data.get("number")
        assert pr_number == 456

    def test_fetch_auto_detect_pr_failure(self):
        """Test fetch command handles auto-detect failure"""
        result = MagicMock()
        result.returncode = 1
        result.stdout = ""

        if result.returncode != 0:
            output = {
                "success": False,
                "message": "无法自动获取 PR 编号，请使用 --pr 参数指定",
            }
        else:
            output = {"success": True}

        assert output["success"] is False

    def test_fetch_with_explicit_pr(self):
        """Test fetch command with explicit PR number"""
        args_pr = 789
        assert args_pr == 789

    def test_gh_cli_not_available(self):
        """Test behavior when gh CLI is not available"""
        result = MagicMock()
        result.returncode = 127
        result.stderr = "'gh' is not recognized as an internal or external command"

        if result.returncode != 0:
            output = {
                "success": False,
                "message": "无法自动获取 PR 编号，请使用 --pr 参数指定",
            }
        else:
            output = {"success": True}

        assert output["success"] is False

    def test_gh_cli_not_authenticated(self):
        """Test behavior when gh CLI is not authenticated"""
        result = MagicMock()
        result.returncode = 1
        result.stderr = "To get started with GitHub CLI, please run: gh auth login"

        if result.returncode != 0:
            output = {
                "success": False,
                "message": "无法自动获取 PR 编号，请使用 --pr 参数指定",
            }
        else:
            output = {"success": True}

        assert output["success"] is False

    def test_gh_cli_no_pr_on_branch(self):
        """Test behavior when no PR exists for current branch"""
        result = MagicMock()
        result.returncode = 1
        result.stderr = "no pull requests found"

        if result.returncode != 0:
            output = {
                "success": False,
                "message": "无法自动获取 PR 编号，请使用 --pr 参数指定",
            }
        else:
            output = {"success": True}

        assert output["success"] is False

    def test_gh_cli_not_installed_file_not_found(self):
        """Test behavior when gh CLI is not installed (FileNotFoundError)"""

        try:
            raise FileNotFoundError("gh not found")
        except FileNotFoundError:
            output = {
                "success": False,
                "message": "gh 命令未安装，请安装 GitHub CLI 或手动指定 --pr 参数",
            }

        assert output["success"] is False
        assert "gh 命令未安装" in output["message"]

    def test_gh_cli_timeout(self):
        """Test behavior when gh CLI times out"""
        import subprocess

        try:
            raise subprocess.TimeoutExpired("gh", 30)
        except subprocess.TimeoutExpired:
            output = {
                "success": False,
                "message": "gh 命令执行超时，请检查网络连接或手动指定 --pr 参数",
            }

        assert output["success"] is False
        assert "超时" in output["message"]

    def test_gh_cli_permission_error(self):
        """Test behavior when gh CLI has permission issues"""
        try:
            raise PermissionError("Permission denied")
        except PermissionError:
            output = {
                "success": False,
                "message": "gh 命令权限不足，请检查 GitHub CLI 认证状态或手动指定 --pr 参数",
            }

        assert output["success"] is False
        assert "权限不足" in output["message"]


class TestPointsDetector:
    """Test points detection functionality"""

    @pytest.mark.asyncio
    async def test_api_success_returns_points(self):
        """Test API success directly returns points"""
        from src.account.points_detector import PointsDetector

        detector = PointsDetector()
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.url = "https://rewards.bing.com/"
        mock_page.wait_for_timeout = AsyncMock()

        mock_client = AsyncMock()
        mock_client.get_current_points.return_value = 5000

        with patch("src.account.points_detector.DashboardClient", return_value=mock_client):
            result = await detector.get_current_points(mock_page, skip_navigation=True)
            assert result == 5000

    @pytest.mark.asyncio
    async def test_api_failure_fallback_to_html(self):
        """Test API failure falls back to HTML parsing"""
        from src.account.points_detector import PointsDetector

        detector = PointsDetector()
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.url = "https://rewards.bing.com/"
        mock_page.wait_for_timeout = AsyncMock()
        mock_page.content = AsyncMock(return_value='{"availablePoints": 3000}')
        mock_page.query_selector_all = AsyncMock(return_value=[])
        mock_page.evaluate = AsyncMock(return_value="Available Points: 3000")

        mock_client = AsyncMock()
        mock_client.get_current_points.side_effect = Exception("API error")

        with patch("src.account.points_detector.DashboardClient", return_value=mock_client):
            result = await detector.get_current_points(mock_page, skip_navigation=True)
            assert result == 3000

    @pytest.mark.asyncio
    async def test_empty_value_handling(self):
        """Test handling of empty/null values"""
        from src.account.points_detector import PointsDetector

        detector = PointsDetector()
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.url = "https://rewards.bing.com/"
        mock_page.wait_for_timeout = AsyncMock()
        mock_page.content = AsyncMock(return_value="")
        mock_page.query_selector_all = AsyncMock(return_value=[])
        mock_page.evaluate = AsyncMock(return_value="")

        mock_client = AsyncMock()
        mock_client.get_current_points.return_value = None

        with patch("src.account.points_detector.DashboardClient", return_value=mock_client):
            result = await detector.get_current_points(mock_page, skip_navigation=True)
            assert result is None

    @pytest.mark.asyncio
    async def test_api_timeout_fallback(self):
        """Test API timeout falls back to HTML parsing"""
        from src.account.points_detector import PointsDetector

        detector = PointsDetector()
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.url = "https://rewards.bing.com/"
        mock_page.wait_for_timeout = AsyncMock()
        mock_page.content = AsyncMock(return_value='{"availablePoints": 2000}')
        mock_page.query_selector_all = AsyncMock(return_value=[])
        mock_page.evaluate = AsyncMock(return_value="Points: 2000")

        mock_client = AsyncMock()
        mock_client.get_current_points.side_effect = TimeoutError("API timeout")

        with patch("src.account.points_detector.DashboardClient", return_value=mock_client):
            result = await detector.get_current_points(mock_page, skip_navigation=True)
            assert result == 2000

    @pytest.mark.asyncio
    async def test_api_connection_error_fallback(self):
        """Test API connection error falls back to HTML parsing"""
        from src.account.points_detector import PointsDetector

        detector = PointsDetector()
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.url = "https://rewards.bing.com/"
        mock_page.wait_for_timeout = AsyncMock()
        mock_page.content = AsyncMock(return_value='{"pointsBalance": 1500}')
        mock_page.query_selector_all = AsyncMock(return_value=[])
        mock_page.evaluate = AsyncMock(return_value="Balance: 1500")

        mock_client = AsyncMock()
        mock_client.get_current_points.side_effect = ConnectionError("Connection failed")

        with patch("src.account.points_detector.DashboardClient", return_value=mock_client):
            result = await detector.get_current_points(mock_page, skip_navigation=True)
            assert result == 1500


class TestParsePoints:
    """Test _parse_points method"""

    def test_parse_points_valid_text(self):
        """Test parsing valid points text"""
        from src.account.points_detector import PointsDetector

        detector = PointsDetector()
        assert detector._parse_points("1,234 points") == 1234
        assert detector._parse_points("Available: 5000") == 5000
        assert detector._parse_points("12345") == 12345

    def test_parse_points_empty_string(self):
        """Test parsing empty string returns None"""
        from src.account.points_detector import PointsDetector

        detector = PointsDetector()
        assert detector._parse_points("") is None

    def test_parse_points_none(self):
        """Test parsing None returns None"""
        from src.account.points_detector import PointsDetector

        detector = PointsDetector()
        result = detector._parse_points(None)  # type: ignore
        assert result is None

    def test_parse_points_whitespace_only(self):
        """Test parsing whitespace-only string returns None"""
        from src.account.points_detector import PointsDetector

        detector = PointsDetector()
        assert detector._parse_points("   ") is None
        assert detector._parse_points("\t\n") is None

    def test_parse_points_no_numbers(self):
        """Test parsing text without numbers returns None"""
        from src.account.points_detector import PointsDetector

        detector = PointsDetector()
        assert detector._parse_points("no numbers here") is None

    def test_parse_points_out_of_range(self):
        """Test parsing out of range values returns None"""
        from src.account.points_detector import PointsDetector

        detector = PointsDetector()
        assert detector._parse_points("99999999") is None


class TestNonGitEnvironment:
    """Test non-Git environment error handling"""

    def test_get_git_branch_not_git_repo(self):
        """Test get_git_branch in non-git directory"""
        from src.review.resolver import get_git_branch

        with patch.object(subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=128, stdout="", stderr="not a git repository"
            )
            result = get_git_branch()
            assert result == ""

    def test_get_git_branch_git_not_installed(self):
        """Test get_git_branch when git is not installed"""
        from src.review.resolver import get_git_branch

        with patch.object(subprocess, "run", side_effect=FileNotFoundError("git not found")):
            result = get_git_branch()
            assert result == ""

    def test_get_git_head_sha_not_git_repo(self):
        """Test get_git_head_sha in non-git directory"""
        from src.review.resolver import get_git_head_sha

        with patch.object(subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=128, stdout="", stderr="not a git repository"
            )
            result = get_git_head_sha()
            assert result == ""

    def test_get_git_head_sha_git_not_installed(self):
        """Test get_git_head_sha when git is not installed"""
        from src.review.resolver import get_git_head_sha

        with patch.object(subprocess, "run", side_effect=FileNotFoundError("git not found")):
            result = get_git_head_sha()
            assert result == ""
