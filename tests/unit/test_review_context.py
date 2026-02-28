import subprocess
from unittest.mock import MagicMock, patch

from review.models import ReviewMetadata
from review.resolver import get_git_branch, get_git_head_sha


class TestGetGitBranch:
    """测试 get_git_branch 函数"""

    def test_get_branch_success(self):
        """测试成功获取分支名称"""
        with patch.object(subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="feature-test-branch\n", stderr=""
            )
            result = get_git_branch()
            assert result == "feature-test-branch"

    def test_get_branch_failure(self):
        """测试获取分支失败"""
        with patch.object(subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            result = get_git_branch()
            assert result == ""

    def test_get_branch_exception(self):
        """测试获取分支异常"""
        with patch.object(subprocess, "run", side_effect=Exception("test error")):
            result = get_git_branch()
            assert result == ""


class TestGetGitHeadSha:
    """测试 get_git_head_sha 函数"""

    def test_get_sha_success(self):
        """测试成功获取 SHA"""
        with patch.object(subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="abc1234\n", stderr="")
            result = get_git_head_sha()
            assert result == "abc1234"

    def test_get_sha_failure(self):
        """测试获取 SHA 失败"""
        with patch.object(subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            result = get_git_head_sha()
            assert result == ""

    def test_get_sha_exception(self):
        """测试获取 SHA 异常"""
        with patch.object(subprocess, "run", side_effect=Exception("test error")):
            result = get_git_head_sha()
            assert result == ""


class TestReviewMetadataBranch:
    """测试 ReviewMetadata 分支字段"""

    def test_metadata_with_branch(self):
        """测试带分支信息的 metadata"""
        metadata = ReviewMetadata(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            branch="feature-test",
            head_sha="abc1234",
        )
        assert metadata.branch == "feature-test"
        assert metadata.head_sha == "abc1234"
        assert metadata.version == "2.3"

    def test_metadata_without_branch(self):
        """测试不带分支信息的 metadata（兼容旧版本）"""
        metadata = ReviewMetadata(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
        )
        assert metadata.branch == ""
        assert metadata.head_sha == ""
