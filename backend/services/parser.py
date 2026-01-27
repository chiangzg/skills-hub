"""
SKILL.md 解析器
"""
import re
import yaml
from pathlib import Path
from typing import Optional

from schemas.skill import SkillMetadata
from core import logger


class SkillParser:
    """SKILL.md 文件解析器"""

    FRONT_MATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n(.*)$', re.DOTALL)

    def parse_file(self, file_path: Path) -> SkillMetadata:
        """
        解析 SKILL.md 文件

        Args:
            file_path: SKILL.md 文件路径

        Returns:
            SkillMetadata 对象
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            return self.parse_content(content)
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return SkillMetadata()

    def parse_content(self, content: str) -> SkillMetadata:
        """
        解析 SKILL.md 内容

        格式：
        ---
        name: "技能名称"
        description: "技能描述"
        tags: ["tag1", "tag2"]
        ---
        详细内容...
        """
        if not content:
            return SkillMetadata()

        match = self.FRONT_MATTER_PATTERN.match(content)
        if not match:
            logger.debug("No front matter found in SKILL.md")
            return SkillMetadata()

        front_matter = match.group(1)

        try:
            metadata = yaml.safe_load(front_matter)
            if not isinstance(metadata, dict):
                return SkillMetadata()

            return SkillMetadata(
                name=metadata.get('name'),
                description=metadata.get('description'),
                tags=metadata.get('tags', [])
            )
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse YAML front matter: {e}")
            return SkillMetadata()

    def has_skill_marker(self, directory: Path) -> bool:
        """
        检查目录是否包含 SKILL.md 文件

        Args:
            directory: 目录路径

        Returns:
            是否包含 SKILL.md
        """
        skill_md = directory / "SKILL.md"
        return skill_md.is_file()


skill_parser = SkillParser()
