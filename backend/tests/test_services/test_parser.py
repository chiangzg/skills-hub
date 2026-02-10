"""
SKILL.md Parser 测试用例
"""
import pytest
from pathlib import Path
from services.parser import skill_parser, SkillParser


class TestSkillParser:
    """SkillParser 测试类"""

    def test_parse_valid_skill_metadata(self, tmp_path):
        """测试解析有效的 SKILL.md 文件"""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("""---
name: "Test Skill"
description: "A test skill description"
tags: ["python", "testing"]
---

# Test Skill Content

This is the content of the skill.
""", encoding="utf-8")

        result = skill_parser.parse_file(skill_md)

        assert result.name == "Test Skill"
        assert result.description == "A test skill description"
        assert result.tags == ["python", "testing"]

    def test_parse_skill_with_empty_front_matter(self, tmp_path):
        """测试空 front matter"""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("---\n---\nContent", encoding="utf-8")

        result = skill_parser.parse_file(skill_md)

        assert result.name is None
        assert result.description is None
        assert result.tags == []

    def test_parse_skill_without_front_matter(self, tmp_path):
        """测试没有 front matter 的文件"""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("# Just content\n\nNo front matter here.", encoding="utf-8")

        result = skill_parser.parse_file(skill_md)

        assert result.name is None
        assert result.description is None

    def test_parse_skill_with_invalid_yaml(self, tmp_path):
        """测试无效的 YAML front matter"""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("""---
name: "Unclosed string
description: test
---
Content""", encoding="utf-8")

        result = skill_parser.parse_file(skill_md)

        # Should return empty metadata on error
        assert result.name is None
        assert result.description is None

    def test_parse_skill_with_partial_metadata(self, tmp_path):
        """测试只有部分元数据的 SKILL.md"""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("""---
name: "Partial Skill"
---
Content""", encoding="utf-8")

        result = skill_parser.parse_file(skill_md)

        assert result.name == "Partial Skill"
        assert result.description is None
        assert result.tags == []

    def test_parse_nonexistent_file(self, tmp_path):
        """测试读取不存在的文件"""
        fake_skill = tmp_path / "nonexistent" / "SKILL.md"

        result = skill_parser.parse_file(fake_skill)

        # Should return empty metadata on error
        assert result.name is None
        assert result.description is None

    def test_parse_content_with_tags_list(self, tmp_path):
        """测试标签解析"""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("""---
name: "Tagged Skill"
tags: ["python", "fastapi", "database"]
---
Content""", encoding="utf-8")

        result = skill_parser.parse_file(skill_md)

        assert result.tags == ["python", "fastapi", "database"]

    def test_has_skill_marker(self, tmp_path):
        """测试 has_skill_marker 方法"""
        with_skill = tmp_path / "with_skill"
        with_skill.mkdir()
        (with_skill / "SKILL.md").touch()

        without_skill = tmp_path / "without_skill"
        without_skill.mkdir()

        assert skill_parser.has_skill_marker(with_skill) is True
        assert skill_parser.has_skill_marker(without_skill) is False

    def test_front_matter_pattern(self):
        """测试 front matter 正则表达式"""
        parser = SkillParser()

        # Valid front matter
        valid_content = """---
name: test
---
content"""
        assert parser.FRONT_MATTER_PATTERN.match(valid_content) is not None

        # No front matter
        no_front_matter = "Just content"
        assert parser.FRONT_MATTER_PATTERN.match(no_front_matter) is None

        # Malformed front matter
        malformed = "---\nname: test\ncontent"
        assert parser.FRONT_MATTER_PATTERN.match(malformed) is None
