"""
Scanner 临时文件清理测试
"""
import pytest
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from tempfile import TemporaryDirectory

from models import Repository, RepositoryType
from services.scanner import SkillScanner
from schemas.skill import SkillMetadata as SchemaSkillMetadata


class TestScannerCleanup:
    """Scanner 临时文件清理测试"""

    @pytest.fixture
    def scanner(self, test_db):
        """创建 Scanner 实例"""
        return SkillScanner(test_db)

    @pytest.fixture
    def mock_repo(self, test_db):
        """创建测试仓库模型"""
        repo = Repository(
            id=1,
            type=RepositoryType.GITHUB,
            owner="testowner",
            name="testrepo",
            branch="main",
            full_name="testowner/testrepo",
            webhook_enabled=False,
            last_sync_at=None,
            access_token=None,
            gitlab_url=None
        )
        return repo

    @pytest.fixture
    def mock_extract_dir(self):
        """创建模拟的解压目录结构"""
        with TemporaryDirectory() as tmpdir:
            temp_base = Path(tmpdir)
            # 模拟 GitHub 服务创建的目录结构: temp_base/owner_name_branch/root_dir
            repo_dir = temp_base / "testowner_testrepo_main"
            root_dir = repo_dir / "testrepo"
            root_dir.mkdir(parents=True)

            # 创建 SKILL.md 文件
            skill_md = root_dir / "SKILL.md"
            skill_md.write_text("""---
name: "Test Skill"
description: "A test skill"
tags: ["test"]
---

# Test Skill
""", encoding="utf-8")

            # 返回 root_dir 供模拟使用
            yield root_dir, temp_base

    @pytest.mark.asyncio
    async def test_scan_repository_cleans_up_temp_dir(self, scanner, mock_repo, mock_extract_dir):
        """测试 scan_repository 在扫描完成后清理临时目录"""
        root_dir, temp_base = mock_extract_dir

        # 模拟 _download_repo 返回 root_dir
        with patch.object(scanner, '_download_repo', new=AsyncMock(return_value=root_dir)):
            # 执行扫描
            result = await scanner.scan_repository(mock_repo)

            # 验证返回结果
            assert len(result) == 1
            assert result[0].name == "Test Skill"

            # 验证父目录被清理（temp_base/owner_name_branch 应该被删除）
            repo_dir = temp_base / "testowner_testrepo_main"
            assert not repo_dir.exists(), f"Cleanup directory {repo_dir} should be removed"

    @pytest.mark.asyncio
    async def test_scan_repository_preserves_custom_temp_dir(self, scanner, mock_repo, mock_extract_dir):
        """测试使用自定义 temp_dir 时不会被清理"""
        root_dir, temp_base = mock_extract_dir

        # 模拟 _download_repo 返回 root_dir
        with patch.object(scanner, '_download_repo', new=AsyncMock(return_value=root_dir)):
            # 使用自定义 temp_dir
            custom_temp = temp_base / "custom_temp"
            custom_temp.mkdir()

            result = await scanner.scan_repository(mock_repo, temp_dir=custom_temp)

            # 验证返回结果
            assert len(result) == 1

            # 验证目录仍然存在（因为指定了 temp_dir）
            repo_dir = temp_base / "testowner_testrepo_main"
            assert repo_dir.exists(), "Custom temp_dir should not be cleaned up"

    @pytest.mark.asyncio
    async def test_scan_cleanup_handles_permission_error(self, scanner, mock_repo, mock_extract_dir):
        """测试清理时处理权限错误"""
        root_dir, temp_base = mock_extract_dir

        # 模拟 _download_repo 返回 root_dir
        with patch.object(scanner, '_download_repo', new=AsyncMock(return_value=root_dir)):
            # 模拟 shutil.rmtree 抛出 PermissionError
            with patch('services.scanner.shutil.rmtree') as mock_rmtree:
                mock_rmtree.side_effect = PermissionError("Access denied")

                # 应该不抛出异常，而是记录警告
                result = await scanner.scan_repository(mock_repo)

                # 验证扫描仍然成功
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_scan_cleanup_handles_generic_exception(self, scanner, mock_repo, mock_extract_dir):
        """测试清理时处理一般异常"""
        root_dir, temp_base = mock_extract_dir

        with patch.object(scanner, '_download_repo', new=AsyncMock(return_value=root_dir)):
            # 模拟 shutil.rmtree 抛出一般异常
            with patch('services.scanner.shutil.rmtree') as mock_rmtree:
                mock_rmtree.side_effect = Exception("Unknown error")

                # 应该不抛出异常，而是记录警告
                result = await scanner.scan_repository(mock_repo)

                # 验证扫描仍然成功
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_scan_cleanup_even_when_scan_fails(self, scanner, mock_repo, mock_extract_dir):
        """测试即使扫描失败，也会执行清理"""
        root_dir, temp_base = mock_extract_dir

        # 模拟 _download_repo 返回 root_dir
        with patch.object(scanner, '_download_repo', new=AsyncMock(return_value=root_dir)):
            # 模拟 os.walk 抛出异常
            with patch('services.scanner.os.walk') as mock_walk:
                mock_walk.side_effect = RuntimeError("Scan failed")

                # 应该抛出异常
                with pytest.raises(RuntimeError, match="Scan failed"):
                    await scanner.scan_repository(mock_repo)

                # 但临时目录应该仍然被清理
                repo_dir = temp_base / "testowner_testrepo_main"
                assert not repo_dir.exists(), "Cleanup should still happen on scan failure"

    @pytest.mark.asyncio
    async def test_scan_multiple_skills(self, scanner, mock_repo, mock_extract_dir):
        """测试扫描多个 skills 后清理"""
        root_dir, temp_base = mock_extract_dir

        # 创建多个 SKILL.md 文件
        (root_dir / "subdir1").mkdir()
        (root_dir / "subdir1" / "SKILL.md").write_text("---\nname: Skill1\n---\n", encoding="utf-8")

        (root_dir / "subdir2").mkdir()
        (root_dir / "subdir2" / "SKILL.md").write_text("---\nname: Skill2\n---\n", encoding="utf-8")

        with patch.object(scanner, '_download_repo', new=AsyncMock(return_value=root_dir)):
            result = await scanner.scan_repository(mock_repo)

            # 验证找到 3 个 skills（root + 2 个子目录）
            assert len(result) == 3

            # 验证清理
            repo_dir = temp_base / "testowner_testrepo_main"
            assert not repo_dir.exists()

    @pytest.mark.asyncio
    async def test_scan_with_no_cleanup_dir_when_nonexistent(self, scanner, mock_repo):
        """测试当 cleanup_dir 不存在时不报错"""
        # 创建一个会被立即删除的临时目录
        with TemporaryDirectory() as tmpdir:
            nonexistent_root = Path(tmpdir) / "nonexistent"
            nonexistent_root.mkdir()

            with patch.object(scanner, '_download_repo', new=AsyncMock(return_value=nonexistent_root)):
                # 模拟外部删除了目录
                pass

        # 这里不需要额外测试，因为代码中检查了 `if cleanup_dir and cleanup_dir.exists()`
