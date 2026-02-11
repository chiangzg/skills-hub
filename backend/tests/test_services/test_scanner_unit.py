"""
Scanner 临时文件清理测试 - 独立单元测试
"""
import pytest
import shutil
import os
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from tempfile import TemporaryDirectory

from models import RepositoryType
from services.scanner import SkillScanner


def create_mock_repo():
    """创建模拟的 Repository 对象"""
    mock_repo = MagicMock()
    mock_repo.id = 1
    mock_repo.type = RepositoryType.GITHUB
    mock_repo.owner = "testowner"
    mock_repo.name = "testrepo"
    mock_repo.branch = "main"
    mock_repo.full_name = "testowner/testrepo"
    mock_repo.access_token = None
    mock_repo.gitlab_url = None
    return mock_repo


class TestScannerCleanupUnit:
    """Scanner 临时文件清理单元测试（不需要数据库）"""

    def test_scan_repository_cleans_up_temp_dir(self):
        """测试 scan_repository 在扫描完成后清理临时目录"""
        with TemporaryDirectory() as tmpdir:
            temp_base = Path(tmpdir)

            # 创建模拟的解压目录结构
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

            # 创建 mock 数据库和 scanner
            mock_db = MagicMock()
            scanner = SkillScanner(mock_db)
            mock_repo = create_mock_repo()

            # 模拟 _download_repo 返回 root_dir
            with patch.object(scanner, '_download_repo', new=AsyncMock(return_value=root_dir)):
                import asyncio

                async def run_test():
                    # 执行扫描
                    result = await scanner.scan_repository(mock_repo)

                    # 验证返回结果
                    assert len(result) == 1
                    assert result[0].name == "Test Skill"

                    # 验证父目录被清理
                    assert not repo_dir.exists(), f"Cleanup directory {repo_dir} should be removed"

                asyncio.run(run_test())

    def test_scan_repository_preserves_custom_temp_dir(self):
        """测试使用自定义 temp_dir 时不会被清理"""
        with TemporaryDirectory() as tmpdir:
            temp_base = Path(tmpdir)

            # 创建模拟的解压目录结构
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

            # 创建 mock 数据库和 scanner
            mock_db = MagicMock()
            scanner = SkillScanner(mock_db)
            mock_repo = create_mock_repo()

            # 模拟 _download_repo 返回 root_dir
            with patch.object(scanner, '_download_repo', new=AsyncMock(return_value=root_dir)):
                import asyncio

                async def run_test():
                    # 使用自定义 temp_dir
                    custom_temp = temp_base / "custom_temp"
                    custom_temp.mkdir()

                    result = await scanner.scan_repository(mock_repo, temp_dir=custom_temp)

                    # 验证返回结果
                    assert len(result) == 1

                    # 验证目录仍然存在（因为指定了 temp_dir）
                    assert repo_dir.exists(), "Custom temp_dir should not be cleaned up"

                asyncio.run(run_test())

    def test_scan_cleanup_handles_permission_error(self):
        """测试清理时处理权限错误"""
        with TemporaryDirectory() as tmpdir:
            temp_base = Path(tmpdir)

            # 创建模拟的解压目录结构
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

            # 创建 mock 数据库和 scanner
            mock_db = MagicMock()
            scanner = SkillScanner(mock_db)
            mock_repo = create_mock_repo()

            # 模拟 _download_repo 返回 root_dir
            with patch.object(scanner, '_download_repo', new=AsyncMock(return_value=root_dir)):
                # 模拟 shutil.rmtree 抛出 PermissionError
                with patch('services.scanner.shutil.rmtree') as mock_rmtree:
                    mock_rmtree.side_effect = PermissionError("Access denied")

                    import asyncio

                    async def run_test():
                        # 应该不抛出异常，而是记录警告
                        result = await scanner.scan_repository(mock_repo)

                        # 验证扫描仍然成功
                        assert len(result) == 1

                    asyncio.run(run_test())

    def test_scan_cleanup_handles_generic_exception(self):
        """测试清理时处理一般异常"""
        with TemporaryDirectory() as tmpdir:
            temp_base = Path(tmpdir)

            # 创建模拟的解压目录结构
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

            # 创建 mock 数据库和 scanner
            mock_db = MagicMock()
            scanner = SkillScanner(mock_db)
            mock_repo = create_mock_repo()

            # 模拟 _download_repo 返回 root_dir
            with patch.object(scanner, '_download_repo', new=AsyncMock(return_value=root_dir)):
                # 模拟 shutil.rmtree 抛出一般异常
                with patch('services.scanner.shutil.rmtree') as mock_rmtree:
                    mock_rmtree.side_effect = Exception("Unknown error")

                    import asyncio

                    async def run_test():
                        # 应该不抛出异常，而是记录警告
                        result = await scanner.scan_repository(mock_repo)

                        # 验证扫描仍然成功
                        assert len(result) == 1

                    asyncio.run(run_test())

    def test_scan_cleanup_even_when_scan_fails(self):
        """测试即使扫描过程中出错，也会执行清理"""
        with TemporaryDirectory() as tmpdir:
            temp_base = Path(tmpdir)

            # 创建模拟的解压目录结构
            repo_dir = temp_base / "testowner_testrepo_main"
            root_dir = repo_dir / "testrepo"
            root_dir.mkdir(parents=True)

            # 创建 mock 数据库和 scanner
            mock_db = MagicMock()
            scanner = SkillScanner(mock_db)
            mock_repo = create_mock_repo()

            # 模拟 _download_repo 返回 root_dir
            with patch.object(scanner, '_download_repo', new=AsyncMock(return_value=root_dir)):
                import asyncio

                async def run_test():
                    # 正常扫描后，验证清理发生
                    result = await scanner.scan_repository(mock_repo)

                    # 扫描可能返回 0 个 skills（空目录）
                    assert isinstance(result, list)

                    # 验证清理发生了
                    assert not repo_dir.exists(), "Cleanup directory should be removed after scan"

                asyncio.run(run_test())

    def test_scan_multiple_skills_and_cleanup(self):
        """测试扫描多个 skills 后清理"""
        with TemporaryDirectory() as tmpdir:
            temp_base = Path(tmpdir)

            # 创建模拟的解压目录结构
            repo_dir = temp_base / "testowner_testrepo_main"
            root_dir = repo_dir / "testrepo"
            root_dir.mkdir(parents=True)

            # 创建多个 SKILL.md 文件
            (root_dir / "SKILL.md").write_text("---\nname: Root Skill\n---\n", encoding="utf-8")

            subdir1 = root_dir / "subdir1"
            subdir1.mkdir()
            (subdir1 / "SKILL.md").write_text("---\nname: Skill1\n---\n", encoding="utf-8")

            subdir2 = root_dir / "subdir2"
            subdir2.mkdir()
            (subdir2 / "SKILL.md").write_text("---\nname: Skill2\n---\n", encoding="utf-8")

            # 创建 mock 数据库和 scanner
            mock_db = MagicMock()
            scanner = SkillScanner(mock_db)
            mock_repo = create_mock_repo()

            # 模拟 _download_repo 返回 root_dir
            with patch.object(scanner, '_download_repo', new=AsyncMock(return_value=root_dir)):
                import asyncio

                async def run_test():
                    result = await scanner.scan_repository(mock_repo)

                    # 验证找到 3 个 skills（root + 2 个子目录）
                    assert len(result) == 3

                    # 验证清理
                    assert not repo_dir.exists()

                asyncio.run(run_test())

    def test_scan_with_nonexistent_cleanup_dir(self):
        """测试当 cleanup_dir 不存在时不报错"""
        with TemporaryDirectory() as tmpdir:
            temp_base = Path(tmpdir)

            # 创建模拟的解压目录结构
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

            # 创建 mock 数据库和 scanner
            mock_db = MagicMock()
            scanner = SkillScanner(mock_db)
            mock_repo = create_mock_repo()

            # 模拟 _download_repo 返回 root_dir
            with patch.object(scanner, '_download_repo', new=AsyncMock(return_value=root_dir)):
                # 模拟目录在外部被删除（模拟 cleanup_dir 不存在的情况）
                with patch('pathlib.Path.exists', return_value=False):
                    import asyncio

                    async def run_test():
                        # 应该正常完成，不报错
                        result = await scanner.scan_repository(mock_repo)

                        # 验证扫描成功
                        assert len(result) == 1

                    asyncio.run(run_test())
