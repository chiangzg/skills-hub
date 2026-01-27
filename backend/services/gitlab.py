"""
GitLab 仓库服务
"""
import aiofiles
import os
import zipfile
from pathlib import Path
from typing import Optional
from urllib.parse import quote
import httpx

from core import logger, ExternalServiceError


class GitLabService:
    """GitLab 仓库服务"""

    def __init__(self, gitlab_url: Optional[str] = None):
        """
        Args:
            gitlab_url: GitLab 实例地址，如 https://gitlab.example.com
                      如果为空，使用默认的 gitlab.com
        """
        self.base_url = (gitlab_url or "https://gitlab.com").rstrip('/')
        self.api_base = f"{self.base_url}/api/v4"

    def get_archive_url(self, owner: str, name: str, branch: str) -> str:
        """获取仓库归档 URL"""
        # GitLab 的归档 URL 格式
        return f"{self.base_url}/{owner}/{name}/-/archive/{branch}/{name}-{branch}.tar.gz"

    def get_archive_zip_url(self, owner: str, name: str, branch: str) -> str:
        """获取仓库归档 ZIP URL（如果有）"""
        return f"{self.base_url}/{owner}/{name}/-/archive/{branch}/{name}-{branch}.zip"

    def get_raw_url(self, owner: str, name: str, branch: str, path: str) -> str:
        """获取原始文件 URL"""
        return f"{self.base_url}/{owner}/{name}/-/raw/{branch}/{path}"

    def get_readme_url(self, owner: str, name: str, branch: str, directory: str = "") -> str:
        """获取 README URL"""
        if directory:
            return f"{self.base_url}/{owner}/{name}/-/tree/{branch}/{directory}"
        return f"{self.base_url}/{owner}/{name}/-/tree/{branch}"

    async def download_repo(
        self,
        owner: str,
        name: str,
        branch: str,
        access_token: Optional[str] = None,
        temp_dir: Optional[Path] = None
    ) -> Path:
        """
        下载 GitLab 仓库归档文件并解压

        Args:
            owner: 仓库所有者（用户名或组名）
            name: 仓库名称
            branch: 分支名
            access_token: 访问令牌（私有仓库需要）
            temp_dir: 临时目录

        Returns:
            解压后的目录路径
        """
        import tempfile
        import tarfile

        if temp_dir is None:
            temp_dir = Path(tempfile.gettempdir())

        # GitLab 通常使用 tar.gz，但也支持 zip
        url = self.get_archive_zip_url(owner, name, branch)
        logger.info(f"Downloading GitLab repo: {owner}/{name} from {url}")

        headers = {}
        if access_token:
            headers["PRIVATE-TOKEN"] = access_token

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                # 如果 ZIP 失败，尝试 tar.gz
                logger.warning(f"ZIP download failed ({e.response.status_code}), trying tar.gz")
                return await self._download_tarball(owner, name, branch, access_token, temp_dir)

                # 如果还是失败
                raise ExternalServiceError("GitLab", f"Failed to download: {e.response.status_code}")

            # 保存 ZIP 文件
            zip_path = temp_dir / f"{owner}_{name}_{branch}.zip"
            async with aiofiles.open(zip_path, "wb") as f:
                await f.write(response.content)

            logger.info(f"Downloaded to {zip_path}, size: {len(response.content)} bytes")

        # 解压 ZIP
        extract_dir = temp_dir / f"{owner}_{name}_{branch}"
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                namelist = zip_ref.namelist()
                if namelist:
                    root_dir = namelist[0].split('/')[0]
                    zip_ref.extractall(extract_dir)

            logger.info(f"Extracted to {extract_dir}")
            return extract_dir / root_dir

        except zipfile.BadZipFile as e:
            raise ExternalServiceError("GitLab", f"Invalid zip file: {e}")
        finally:
            if zip_path.exists():
                zip_path.unlink()

    async def _download_tarball(
        self,
        owner: str,
        name: str,
        branch: str,
        access_token: Optional[str],
        temp_dir: Path
    ) -> Path:
        """下载并解压 tar.gz 文件"""
        import tarfile

        url = self.get_archive_url(owner, name, branch)
        logger.info(f"Downloading GitLab tarball: {url}")

        headers = {}
        if access_token:
            headers["PRIVATE-TOKEN"] = access_token

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("GitLab", f"Failed to download tarball: {e.response.status_code}")

            tar_path = temp_dir / f"{owner}_{name}_{branch}.tar.gz"
            async with aiofiles.open(tar_path, "wb") as f:
                await f.write(response.content)

            logger.info(f"Downloaded tarball to {tar_path}")

        extract_dir = temp_dir / f"{owner}_{name}_{branch}_extract"
        extract_dir.mkdir(exist_ok=True)

        try:
            with tarfile.open(tar_path, 'r:gz') as tar_ref:
                tar_ref.extractall(extract_dir)

            # 找到解压后的根目录
            items = list(extract_dir.iterdir())
            if items:
                return items[0]
            return extract_dir

        finally:
            if tar_path.exists():
                tar_path.unlink()


def get_gitlab_service(gitlab_url: Optional[str] = None) -> GitLabService:
    """获取 GitLab 服务实例"""
    return GitLabService(gitlab_url)
