"""
GitHub 仓库服务
"""
import aiofiles
import os
import zipfile
from pathlib import Path
from typing import Optional
import httpx

from core import logger, ExternalServiceError


class GitHubService:
    """GitHub 仓库服务"""

    def __init__(self):
        self.base_url = "https://github.com"
        self.api_base = "https://api.github.com"
        self.archive_base = "https://github.com"

    def get_archive_url(self, owner: str, name: str, branch: str) -> str:
        """获取仓库归档 URL"""
        return f"{self.archive_base}/{owner}/{name}/archive/refs/heads/{branch}.zip"

    def get_raw_url(self, owner: str, name: str, branch: str, path: str) -> str:
        """获取原始文件 URL"""
        return f"{self.base_url}/{owner}/{name}/raw/{branch}/{path}"

    def get_readme_url(self, owner: str, name: str, branch: str, directory: str = "") -> str:
        """获取 README URL"""
        if directory:
            return f"{self.base_url}/{owner}/{name}/tree/{branch}/{directory}"
        return f"{self.base_url}/{owner}/{name}/tree/{branch}"

    async def download_repo(
        self,
        owner: str,
        name: str,
        branch: str,
        access_token: Optional[str] = None,
        temp_dir: Optional[Path] = None
    ) -> Path:
        """
        下载 GitHub 仓库 ZIP 文件并解压

        Args:
            owner: 仓库所有者
            name: 仓库名称
            branch: 分支名
            access_token: 访问令牌（私有仓库需要）
            temp_dir: 临时目录

        Returns:
            解压后的目录路径
        """
        import tempfile

        if temp_dir is None:
            temp_dir = Path(tempfile.gettempdir())

        url = self.get_archive_url(owner, name, branch)
        logger.info(f"Downloading GitHub repo: {owner}/{name} from {url}")

        headers = {}
        if access_token:
            headers["Authorization"] = f"token {access_token}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("GitHub", f"Failed to download: {e.response.status_code}")

            # 保存 ZIP 文件
            zip_path = temp_dir / f"{owner}_{name}_{branch}.zip"
            async with aiofiles.open(zip_path, "wb") as f:
                await f.write(response.content)

            logger.info(f"Downloaded to {zip_path}, size: {len(response.content)} bytes")

        # 解压
        extract_dir = temp_dir / f"{owner}_{name}_{branch}"
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 获取根目录名称
                namelist = zip_ref.namelist()
                if namelist:
                    root_dir = namelist[0].split('/')[0]
                    zip_ref.extractall(extract_dir)

            logger.info(f"Extracted to {extract_dir}")
            return extract_dir / root_dir

        except zipfile.BadZipFile as e:
            raise ExternalServiceError("GitHub", f"Invalid zip file: {e}")
        finally:
            # 删除 ZIP 文件
            if zip_path.exists():
                zip_path.unlink()


github_service = GitHubService()
