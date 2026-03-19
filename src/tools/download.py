import os
import requests
import subprocess
from typing import List, Dict, Any, Optional
import aria2p

class DownloadManager:
    def __init__(self, host: str = "localhost", port: int = 6800, secret: str = ""):
        if not host.startswith("http"):
            host = f"http://{host}"
        self.host = host
        self.port = port
        self.secret = secret
        self.client = aria2p.API(
            aria2p.Client(host=host, port=port, secret=secret)
        )

    def create_download(self, uri: str, filename: str = None, dir: str = "/downloads") -> Dict[str, Any]:
        """创建下载任务"""
        options = {"dir": dir}
        if filename:
            options["out"] = filename
        download = self.client.add_uris([uri], options=options)
        return {
            "gid": download.gid,
            "name": download.name,
            "status": download.status
        }

    def list_downloads(self, status: str = None) -> List[Dict[str, Any]]:
        """列出下载任务"""
        downloads = self.client.get_downloads()
        if status:
            downloads = [d for d in downloads if d.status == status]
        return [{
            "gid": d.gid,
            "name": d.name,
            "status": d.status,
            "total_length": d.total_length,
            "completed_length": d.completed_length,
            "download_speed": d.download_speed,
            "progress": (d.completed_length / d.total_length * 100) if d.total_length > 0 else 0
        } for d in downloads]

    def pause_download(self, gid: str) -> Dict[str, str]:
        download = self.client.get_download(gid)
        download.pause()
        return {"gid": gid, "status": "paused"}

    def resume_download(self, gid: str) -> Dict[str, str]:
        download = self.client.get_download(gid)
        download.resume()
        return {"gid": gid, "status": "resume"}

    def cancel_download(self, gid: str) -> Dict[str, str]:
        download = self.client.get_download(gid)
        download.remove()
        return {"gid": gid, "status": "removed"}

    def get_download_status(self, gid: str) -> Dict[str, Any]:
        download = self.client.get_download(gid)
        return {
            "gid": download.gid,
            "name": download.name,
            "status": download.status,
            "total_length": download.total_length,
            "completed_length": download.completed_length,
            "download_speed": download.download_speed,
            "upload_speed": download.upload_speed,
            "progress": (download.completed_length / download.total_length * 100) if download.total_length > 0 else 0,
            "error_message": download.error_message
        }

    def get_bt_trackers(self) -> List[str]:
        """获取 BT tracker 列表"""
        opts = self.client.get_global_options()
        return opts.get("bt-tracker", "").split(",") if opts.get("bt-tracker") else []

    def update_bt_trackers(self, source_url: str = "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt") -> Dict[str, Any]:
        """从 URL 获取并更新 BT tracker 列表"""
        try:
            response = requests.get(source_url, timeout=30)
            response.raise_for_status()
            trackers = [t.strip() for t in response.text.strip().split("\n") if t.strip()]
            tracker_str = ",".join(trackers)
            self.client.set_global_options({"bt-tracker": tracker_str})
            return {"trackers": trackers, "count": len(trackers)}
        except Exception as e:
            return {"error": str(e), "trackers": [], "count": 0}

    def restart_aria2(self) -> Dict[str, str]:
        """重启 aria2 服务"""
        try:
            subprocess.run(["pkill", "-HUP", "aria2c"], check=True)
            return {"status": "restarted"}
        except subprocess.CalledProcessError:
            return {"status": "failed", "error": "Failed to restart aria2"}

    def get_global_options(self) -> Dict[str, Any]:
        """获取全局配置"""
        opts = self.client.get_global_options()
        if isinstance(opts, dict):
            return opts
        return opts.get_struct() if hasattr(opts, 'get_struct') else opts._struct

    def set_speed_limit(self, download_limit: str = None, upload_limit: str = None) -> Dict[str, str]:
        """设置速度限制"""
        options = {}
        if download_limit:
            options["max-download-limit"] = download_limit
        if upload_limit:
            options["max-upload-limit"] = upload_limit
        if options:
            self.client.set_global_options(options)
        return options
