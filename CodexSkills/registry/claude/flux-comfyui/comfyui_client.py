"""
ComfyUI Flux.2 生图客户端
通过 ComfyUI REST API 调用本地 Flux.2 Dev 模型实现文生图和图生图

完全本地运行，无需任何 API 密钥或网络请求
"""
import atexit
import json
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path


class ComfyUIFluxClient:
    """封装 ComfyUI Flux.2 Dev 本地生图 workflow"""

    UNET_NAME = "flux2_dev_fp8mixed.safetensors"
    CLIP_NAME = "mistral_3_small_flux2_bf16.safetensors"
    VAE_NAME = "full_encoder_small_decoder.safetensors"
    UPSCALE_MODEL = "4x-UltraSharp.pth"  # AI 4× 放大模型

    def __init__(self, server_url="http://localhost:8188",
                 output_dir=None, timeout=600):
        self.server_url = server_url.rstrip("/")
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent / "flux_outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout

    # ═══════════════════════════════════════════════════════════════
    # 公开接口
    # ═══════════════════════════════════════════════════════════════

    def generate(self, prompt, *, width=1024, height=768,
                 image_paths=None, steps=20, guidance=3.5, seed=None,
                 sampler="euler", scheduler="simple",
                 upscale_model=None,
                 progress_callback=None, cancel_event=None):
        """文生图/图生图入口，返回保存后的本地 PNG 路径

        Args:
            sampler: 采样器，如 "euler", "dpmpp_2m", "dpmpp_sde"
            scheduler: 调度器，如 "simple", "karras"
            upscale_model: 可选，如 "4x-UltraSharp.pth"，启用 AI 4× 放大
            progress_callback: 可选，callable(elapsed_seconds)，每秒调用一次
            cancel_event: 可选，threading.Event，set 后中断生成
        """
        if seed is None:
            import random
            seed = random.randint(0, 2**63 - 1)

        if image_paths:
            image_name = self._upload_image(image_paths[0])
            workflow = self._build_img2img_workflow(
                prompt, image_name, width, height, steps, guidance, seed,
                sampler=sampler, scheduler=scheduler,
                upscale_model=upscale_model)
        else:
            workflow = self._build_txt2img_workflow(
                prompt, width, height, steps, guidance, seed,
                sampler=sampler, scheduler=scheduler,
                upscale_model=upscale_model)

        prompt_id = self._queue_prompt(workflow)
        image_data = self._wait_for_result(prompt_id,
                                           progress_callback=progress_callback,
                                           cancel_event=cancel_event)
        output_path = self._save_image(image_data, prompt_id)
        return str(output_path)

    # ═══════════════════════════════════════════════════════════════
    # 图片上传
    # ═══════════════════════════════════════════════════════════════

    def _upload_image(self, image_path):
        """上传参考图到 ComfyUI input 目录，返回文件名"""
        import io
        import uuid

        ext = Path(image_path).suffix or ".png"
        upload_name = f"flux_ref_{uuid.uuid4().hex[:8]}{ext}"

        with open(image_path, "rb") as f:
            image_data = f.read()

        boundary = "----ComfyUIClientBoundary"
        body = io.BytesIO()
        body.write(f"--{boundary}\r\n".encode())
        body.write(f'Content-Disposition: form-data; name="image"; filename="{upload_name}"\r\n'.encode())
        body.write(f"Content-Type: image/{ext.lstrip('.')}\r\n\r\n".encode())
        body.write(image_data)
        body.write(f"\r\n--{boundary}--\r\n".encode())

        req = urllib.request.Request(
            f"{self.server_url}/upload/image",
            data=body.getvalue(),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("name", upload_name)
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"图片上传失败 ({e.code}): {body_text}") from e

    # ═══════════════════════════════════════════════════════════════
    # Workflow — 文生图
    # ═══════════════════════════════════════════════════════════════

    def _build_txt2img_workflow(self, prompt, width, height, steps, guidance, seed,
                                 sampler="euler", scheduler="simple",
                                 upscale_model=None):
        """本地 Flux.2 Dev txt2img — 可选 AI 放大

        基础节点 1-12: UNETLoader → CLIPLoader → ... → VAEDecode → IMAGE
        若 upscale_model: 13(UpscaleModelLoader) → 14(ImageUpscaleWithModel) → 15(PreviewImage)
        否则: 13(PreviewImage)
        """
        wf = {
            "1": {"class_type": "UNETLoader",
                  "inputs": {"unet_name": self.UNET_NAME, "weight_dtype": "default"}},
            "2": {"class_type": "CLIPLoader",
                  "inputs": {"clip_name": self.CLIP_NAME, "type": "flux2", "device": "default"}},
            "3": {"class_type": "VAELoader",
                  "inputs": {"vae_name": self.VAE_NAME}},
            "4": {"class_type": "CLIPTextEncode",
                  "inputs": {"clip": ["2", 0], "text": prompt}},
            "5": {"class_type": "FluxGuidance",
                  "inputs": {"conditioning": ["4", 0], "guidance": guidance}},
            "6": {"class_type": "BasicGuider",
                  "inputs": {"model": ["1", 0], "conditioning": ["5", 0]}},
            "7": {"class_type": "EmptyFlux2LatentImage",
                  "inputs": {"width": width, "height": height, "batch_size": 1}},
            "8": {"class_type": "RandomNoise",
                  "inputs": {"noise_seed": seed}},
            "9": {"class_type": "Flux2Scheduler",
                  "inputs": {"steps": steps, "width": width, "height": height,
                             "scheduler": scheduler}},
            "10": {"class_type": "KSamplerSelect",
                   "inputs": {"sampler_name": sampler}},
            "11": {"class_type": "SamplerCustomAdvanced",
                   "inputs": {"noise": ["8", 0], "guider": ["6", 0],
                              "sampler": ["10", 0], "sigmas": ["9", 0],
                              "latent_image": ["7", 0]}},
            "12": {"class_type": "VAEDecode",
                   "inputs": {"samples": ["11", 0], "vae": ["3", 0]}},
        }
        if upscale_model:
            wf["13"] = {"class_type": "UpscaleModelLoader",
                       "inputs": {"model_name": upscale_model}}
            wf["14"] = {"class_type": "ImageUpscaleWithModel",
                       "inputs": {"upscale_model": ["13", 0], "image": ["12", 0]}}
            wf["15"] = {"class_type": "PreviewImage",
                       "inputs": {"images": ["14", 0]}}
        else:
            wf["13"] = {"class_type": "PreviewImage",
                       "inputs": {"images": ["12", 0]}}
        return wf

    # ═══════════════════════════════════════════════════════════════
    # Workflow — 图生图
    # ═══════════════════════════════════════════════════════════════

    def _build_img2img_workflow(self, prompt, image_name, width, height, steps, guidance, seed,
                                 sampler="euler", scheduler="simple",
                                 upscale_model=None):
        """本地 Flux.2 Dev img2img — 可选 AI 放大

        基础节点 1-13: UNETLoader → ... → LoadImage → VAEEncode → ... → VAEDecode → IMAGE
        若 upscale_model: 14(UpscaleModelLoader) → 15(ImageUpscaleWithModel) → 16(PreviewImage)
        否则: 14(PreviewImage)
        """
        wf = {
            "1": {"class_type": "UNETLoader",
                  "inputs": {"unet_name": self.UNET_NAME, "weight_dtype": "default"}},
            "2": {"class_type": "CLIPLoader",
                  "inputs": {"clip_name": self.CLIP_NAME, "type": "flux2", "device": "default"}},
            "3": {"class_type": "VAELoader",
                  "inputs": {"vae_name": self.VAE_NAME}},
            "4": {"class_type": "CLIPTextEncode",
                  "inputs": {"clip": ["2", 0], "text": prompt}},
            "5": {"class_type": "FluxGuidance",
                  "inputs": {"conditioning": ["4", 0], "guidance": guidance}},
            "6": {"class_type": "BasicGuider",
                  "inputs": {"model": ["1", 0], "conditioning": ["5", 0]}},
            "7": {"class_type": "LoadImage",
                  "inputs": {"image": image_name}},
            "8": {"class_type": "VAEEncode",
                  "inputs": {"pixels": ["7", 0], "vae": ["3", 0]}},
            "9": {"class_type": "RandomNoise",
                  "inputs": {"noise_seed": seed}},
            "10": {"class_type": "Flux2Scheduler",
                   "inputs": {"steps": steps, "width": width, "height": height,
                              "scheduler": scheduler}},
            "11": {"class_type": "KSamplerSelect",
                   "inputs": {"sampler_name": sampler}},
            "12": {"class_type": "SamplerCustomAdvanced",
                   "inputs": {"noise": ["9", 0], "guider": ["6", 0],
                              "sampler": ["11", 0], "sigmas": ["10", 0],
                              "latent_image": ["8", 0]}},
            "13": {"class_type": "VAEDecode",
                   "inputs": {"samples": ["12", 0], "vae": ["3", 0]}},
        }
        if upscale_model:
            wf["14"] = {"class_type": "UpscaleModelLoader",
                       "inputs": {"model_name": upscale_model}}
            wf["15"] = {"class_type": "ImageUpscaleWithModel",
                       "inputs": {"upscale_model": ["14", 0], "image": ["13", 0]}}
            wf["16"] = {"class_type": "PreviewImage",
                       "inputs": {"images": ["15", 0]}}
        else:
            wf["14"] = {"class_type": "PreviewImage",
                       "inputs": {"images": ["13", 0]}}
        return wf

    # ═══════════════════════════════════════════════════════════════
    # API 通信
    # ═══════════════════════════════════════════════════════════════

    def _queue_prompt(self, workflow):
        """POST /prompt，提交 workflow 到队列，返回 prompt_id"""
        payload = json.dumps({"prompt": workflow}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.server_url}/prompt",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"ComfyUI 返回错误 ({e.code}): {body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"无法连接到 ComfyUI ({self.server_url}): {e.reason}") from e

        if "error" in data:
            raise RuntimeError(f"ComfyUI prompt 错误: {data['error']}")
        if "node_errors" in data and data["node_errors"]:
            raise RuntimeError(f"节点错误: {data['node_errors']}")
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise RuntimeError(f"ComfyUI 未返回 prompt_id: {data}")
        return prompt_id

    def _wait_for_result(self, prompt_id, progress_callback=None, cancel_event=None):
        """轮询 GET /history/{prompt_id} 直到完成，返回图片二进制数据

        Args:
            progress_callback: callable(elapsed_seconds)，每次轮询时调用
            cancel_event: threading.Event，set 后抛出 FluxInterrupted
        """
        start = time.time()
        url = f"{self.server_url}/history/{prompt_id}"

        while time.time() - start < self.timeout:
            # 取消检查
            if cancel_event is not None and cancel_event.is_set():
                # 通知 ComfyUI 中断
                try:
                    interrupt_generation(self.server_url)
                except Exception:
                    pass
                raise FluxInterrupted("用户取消了生图")

            # 进度通知
            elapsed = time.time() - start
            if progress_callback is not None:
                try:
                    progress_callback(elapsed)
                except Exception:
                    pass  # 进度回调不应中断主流程

            try:
                with urllib.request.urlopen(url, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except Exception:
                time.sleep(3)
                continue

            entry = data.get(prompt_id)
            if entry:
                status = entry.get("status", {})
                if status.get("completed") is False:
                    messages = status.get("messages", [])
                    err_text = "; ".join(str(m) for m in messages[-3:]) if messages else "未知错误"
                    raise RuntimeError(f"生图失败: {err_text}")
                if entry.get("outputs"):
                    return self._extract_image(entry["outputs"])
            time.sleep(3)

        raise TimeoutError(f"生图超时（{self.timeout} 秒），prompt_id={prompt_id}")

    def _extract_image(self, outputs):
        """从 ComfyUI history outputs 中提取图片数据"""
        for node_id, node_output in outputs.items():
            images = node_output.get("images", [])
            if images:
                img_info = images[0]
                img_type = img_info.get("type", "output")
                filename = img_info["filename"]
                subfolder = img_info.get("subfolder", "")
                if subfolder:
                    img_url = f"{self.server_url}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
                else:
                    img_url = f"{self.server_url}/view?filename={filename}&type={img_type}"
                with urllib.request.urlopen(img_url, timeout=30) as resp:
                    return resp.read()
        raise RuntimeError("未在输出中找到图片")

    def _save_image(self, image_data, prompt_id):
        """保存图片到本地，返回路径"""
        ts = time.strftime("%Y%m%d_%H%M%S")
        short_id = prompt_id[:8]
        filename = f"flux_{ts}_{short_id}.png"
        filepath = self.output_dir / filename
        filepath.write_bytes(image_data)
        return filepath


# ═══════════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════════

# 全局引用，用于跟踪已启动的 ComfyUI 进程
_comfyui_process = None


def check_comfyui_available(server_url="http://localhost:8188"):
    """快速检查 ComfyUI 是否可用"""
    try:
        with urllib.request.urlopen(f"{server_url}/system_stats", timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def launch_comfyui(comfyui_dir=r"E:\ComfyUI", server_url="http://localhost:8188",
                   python_exe=None):
    """启动 ComfyUI 后台进程，返回 (Popen, port)"""
    global _comfyui_process

    if _comfyui_process is not None and _comfyui_process.poll() is None:
        return _comfyui_process  # 已经在运行

    port = _extract_port(server_url)
    if python_exe is None:
        python_exe = sys.executable  # 使用当前 Python

    _comfyui_process = subprocess.Popen(
        [python_exe, "main.py", "--port", str(port)],
        cwd=comfyui_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    return _comfyui_process


def wait_for_comfyui(server_url="http://localhost:8188", timeout=120):
    """轮询等待 ComfyUI 就绪，返回 True/False"""
    start = time.time()
    while time.time() - start < timeout:
        if check_comfyui_available(server_url):
            return True
        time.sleep(2)
    return False


def shutdown_comfyui():
    """关闭之前由 launch_comfyui 启动的 ComfyUI 进程，释放 GPU 显存"""
    global _comfyui_process
    if _comfyui_process is not None:
        try:
            _comfyui_process.terminate()
            _comfyui_process.wait(timeout=10)
        except Exception:
            try:
                _comfyui_process.kill()
            except Exception:
                pass
        _comfyui_process = None


# 进程退出时兜底清理，防止孤儿进程占用 GPU
atexit.register(shutdown_comfyui)


def _extract_port(server_url):
    """从 URL 提取端口号"""
    if ":" in server_url.split("//")[-1]:
        return int(server_url.split("//")[-1].split(":")[-1].split("/")[0])
    return 8188


def interrupt_generation(server_url="http://localhost:8188"):
    """POST /interrupt 取消当前正在执行的 prompt"""
    req = urllib.request.Request(
        f"{server_url.rstrip('/')}/interrupt",
        method="POST", data=b"",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status == 200


class FluxInterrupted(Exception):
    """生图被用户取消"""
    pass


if __name__ == "__main__":
    if not check_comfyui_available():
        print("ComfyUI 不在线，请先启动 ComfyUI")
        exit(1)

    client = ComfyUIFluxClient()
    print("ComfyUI 在线，使用本地 Flux.2 Dev 生图...")
    try:
        path = client.generate("a cute orange cat sitting on a cloud, cartoon style",
                               width=512, height=512, steps=20)
        print(f"图片已保存: {path}")
    except Exception as e:
        print(f"生成失败: {e}")
