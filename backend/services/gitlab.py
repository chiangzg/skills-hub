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
                      或者 SSH URL 如 git@gitlab.example.com:owner/repo.git
                      如果为空，使用默认的 gitlab.com
        """
        if gitlab_url:
            url = gitlab_url.strip()
            # 处理 SSH URL 格式: git@host:owner/repo.git
            if url.startswith('git@'):
                # 提取主机名: git@gitlab.example.com:xxx -> gitlab.example.com
                colon_pos = url.find(':')
                at_pos = url.find('@')
                if colon_pos > at_pos:
                    url = url[at_pos + 1:colon_pos]

            # 自动添加协议前缀（如果缺失）
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            self.base_url = url.rstrip('/')
        else:
            self.base_url = "https://gitlab.com"
        self.api_base = f"{self.base_url}/api/v4"

    def get_archive_url(self, owner: str, name: str, branch: str) -> str:
        """获取仓库归档 URL"""
        # GitLab 的归档 URL 格式
        return f"{self.base_url}/{owner}/{name}/-/archive/{branch}/{name}-{branch}.tar.gz"

    def get_archive_zip_url(self, owner: str, name: str, branch: str) -> str:
        """获取仓库归档 ZIP URL（如果有）"""
        return f"{self.base_url}/{owner}/{name}/archive/{branch}/{name}-{branch}.zip"

    def get_raw_url(self, owner: str, name: str, branch: str, path: str) -> str:
        """获取原始文件 URL"""
        return f"{self.base_url}/{owner}/{name}/raw/{branch}/{path}"

    def get_readme_url(self, owner: str, name: str, branch: str, directory: str = "") -> str:
        if directory:
            return f"{self.base_url}/{owner}/{name}/tree/{branch}/{directory}"
        return f"{self.base_url}/{owner}/{name}/tree/{branch}"

    async def validate_repository(
        self,
        owner: str,
        name: str,
        branch: str,
        access_token: Optional[str] = None
    ) -> dict:
        """
        验证仓库是否存在，并获取正确的路径信息

        通过 GitLab API 验证仓库，解决 owner 字段存储的是中文显示名称
        而实际 URL 需要使用用户路径的问题。

        Args:
            owner: 仓库所有者（可能是中文显示名称）
            name: 仓库名称
            branch: 分支名
            access_token: 访问令牌（私有仓库需要）

        Returns:
            {
                "exists": bool,
                "path_with_namespace": str,  # 如 "jiangzhiguo/rule-conversion-skill"
                "default_branch": str,
                "web_url": str,
                "owner": str,  # 正确的 owner 路径
                "name": str   # 正确的仓库名称
            }
        """
        headers = {}
        if access_token:
            headers["PRIVATE-TOKEN"] = access_token

        # 构建搜索查询 - 使用 owner/name 格式搜索
        search_query = f"{owner}/{name}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # 首先尝试通过路径搜索项目
                params = {"search": name}
                response = await client.get(
                    f"{self.api_base}/projects",
                    headers=headers,
                    params=params
                )

                if response.status_code == 200:
                    projects = response.json()
                    # 在结果中查找匹配的项目
                    for project in projects:
                        project_path = project.get("path_with_namespace", "")
                        # 模糊匹配：检查是否包含 owner 和 name
                        if (name.lower() in project_path.lower() or
                            project_path.endswith(f"/{name}") or
                            project_path == f"{owner}/{name}"):
                            return {
                                "exists": True,
                                "path_with_namespace": project["path_with_namespace"],
                                "default_branch": project.get("default_branch", branch),
                                "web_url": project.get("web_url", ""),
                                "owner": project["path_with_namespace"].split("/")[0],
                                "name": project["path_with_namespace"].split("/")[-1]
                            }

                # 如果搜索没找到，尝试直接访问项目 API
                # URL 编码 owner 和 name 以支持中文
                encoded_owner = quote(owner, safe='')
                encoded_name = quote(name, safe='')
                project_url = f"{self.api_base}/projects/{encoded_owner}%2F{encoded_name}"

                response = await client.get(project_url, headers=headers)

                if response.status_code == 200:
                    project = response.json()
                    path_parts = project["path_with_namespace"].split("/")
                    return {
                        "exists": True,
                        "path_with_namespace": project["path_with_namespace"],
                        "default_branch": project.get("default_branch", branch),
                        "web_url": project.get("web_url", ""),
                        "owner": path_parts[0],
                        "name": path_parts[-1] if len(path_parts) > 1 else name
                    }

                # 仓库不存在
                return {
                    "exists": False,
                    "path_with_namespace": None,
                    "default_branch": branch,
                    "web_url": "",
                    "owner": owner,
                    "name": name
                }

            except httpx.HTTPStatusError as e:
                logger.warning(f"GitLab API validation failed: {e}")
                return {
                    "exists": False,
                    "path_with_namespace": None,
                    "default_branch": branch,
                    "web_url": "",
                    "owner": owner,
                    "name": name
                }
            except Exception as e:
                logger.error(f"GitLab API validation error: {e}")
                # 验证失败时返回原始值，让调用者决定如何处理
                return {
                    "exists": False,
                    "path_with_namespace": None,
                    "default_branch": branch,
                    "web_url": "",
                    "owner": owner,
                    "name": name
                }

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
                try:
                    return await self._download_tarball(owner, name, branch, access_token, temp_dir)
                except Exception:
                    # 如果 tar.gz 也失败，抛出原始错误
                    error_msg = f"Failed to download: HTTP {e.response.status_code}"
                    if not access_token and e.response.status_code == 401:
                        error_msg += ". This may be a private repository. Please provide an access token."
                    raise ExternalServiceError("GitLab", error_msg)

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
                error_msg = f"Failed to download tarball: HTTP {e.response.status_code}"
                if e.response.status_code == 401:
                    if access_token:
                        error_msg += ". The provided access token may be invalid or expired."
                    else:
                        error_msg += ". This may be a private repository. Please provide an access token."
                elif e.response.status_code == 404:
                    error_msg += ". Please check if the repository, owner, and branch name are correct."
                raise ExternalServiceError("GitLab", error_msg)

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
