import shutil, subprocess, zipfile, logging
from pathlib import Path

log = logging.getLogger("asset")

class GitGameDataMaintainer:
    def __init__(self, repo_url: str, base_dir: Path):
        self.repo_url = repo_url
        self.base_dir = base_dir
        self.assets_dir = base_dir / "assets"
        self.gamedata_dir = base_dir / "gamedata"
        
    def is_initialized(self) -> bool:
        # 以你 loader 读取的关键表作为标志
        return (self.gamedata_dir / "excel" / "character_table.json").exists()

    def _run_git(self, args, cwd=None) -> int:
        p = subprocess.Popen(["git"] + args, cwd=cwd,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in p.stdout:
            log.info(line.strip())
        p.wait()
        return p.returncode

    def sync_repo(self) -> bool:
        if not self.repo_url:
            log.warning("未配置 GameDataRepo，跳过 repo 同步")
            return False

        self.assets_dir.parent.mkdir(parents=True, exist_ok=True)

        if self.assets_dir.exists():
            if (self.assets_dir / ".git").exists():
                if self._run_git(["pull"], cwd=self.assets_dir) == 0:
                    return True
                shutil.rmtree(self.assets_dir, ignore_errors=True)
            else:
                shutil.rmtree(self.assets_dir, ignore_errors=True)

        return self._run_git(["clone", "--depth", "1", "--progress", self.repo_url, str(self.assets_dir)]) == 0

    def extract_zip(self) -> bool:
        zip_path = self.assets_dir / "gamedata.zip"
        if not zip_path.exists():
            log.warning("%s 不存在，无法解压", zip_path)
            return False

        self.gamedata_dir.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(self.gamedata_dir)
            return True
        except Exception:
            log.exception("解压失败")
            return False

    def update(self) -> bool:
        ok = self.sync_repo()
        return ok and self.extract_zip()
