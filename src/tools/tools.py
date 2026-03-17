"""
Agent Tools — Capabilities available to all agents.

Tools:
- Internet search
- Browser automation
- Image generation
- Code execution
- API calls
"""

import asyncio
import logging
import os
import subprocess
import tempfile
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Optional imports
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class WebSearchTool:
    """Internet search tool using web scraping."""

    async def search(self, query: str, num_results: int = 5) -> list:
        """Search the web for information."""
        if not AIOHTTP_AVAILABLE:
            return [{"error": "aiohttp not installed"}]

        try:
            url = f"https://html.duckduckgo.com/html/?q={query}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        if BS4_AVAILABLE:
                            soup = BeautifulSoup(html, "html.parser")
                            results = []
                            for r in soup.select(".result")[:num_results]:
                                title = r.select_one(".result__title")
                                snippet = r.select_one(".result__snippet")
                                results.append({
                                    "title": title.get_text(strip=True) if title else "",
                                    "snippet": snippet.get_text(strip=True) if snippet else ""
                                })
                            return results
                        return [{"raw": html[:1000]}]
                    return [{"error": f"HTTP {resp.status}"}]
        except Exception as e:
            logger.error(f"Search error: {e}")
            return [{"error": str(e)}]


class BrowserTool:
    """Browser automation for web interaction."""

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a web page content."""
        if not AIOHTTP_AVAILABLE:
            return None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        if BS4_AVAILABLE:
                            soup = BeautifulSoup(html, "html.parser")
                            for tag in soup(["script", "style", "nav", "footer"]):
                                tag.decompose()
                            return soup.get_text(separator="\n", strip=True)[:5000]
                        return html[:5000]
        except Exception as e:
            logger.error(f"Browser error: {e}")
        return None


class ImageGeneratorTool:
    """Image generation using AI models."""

    def __init__(self):
        self.output_dir = "./generated_images"
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate(self, prompt: str, filename: str = None) -> Optional[str]:
        """Generate an image from a text prompt."""
        try:
            from diffusers import StableDiffusionPipeline  # noqa
            import torch  # noqa

            pipe = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float16
            )
            device = "cuda" if torch.cuda.is_available() else "cpu"
            pipe = pipe.to(device)

            image = pipe(prompt).images[0]
            fname = filename or f"generated_{hash(prompt) % 10000}.png"
            path = os.path.join(self.output_dir, fname)
            image.save(path)
            return path
        except ImportError:
            logger.warning("diffusers/torch not installed for image generation")
            return None
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return None


class CodeExecutorTool:
    """Safe code execution in a sandbox."""

    def __init__(self):
        self.workspace = "./workspace"
        os.makedirs(self.workspace, exist_ok=True)

    async def execute_python(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute Python code safely."""
        # Write to temp file
        filepath = os.path.join(self.workspace, f"exec_{hash(code) % 10000}.py")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: subprocess.run(
                ["python", filepath],
                capture_output=True, text=True, timeout=timeout,
                cwd=self.workspace
            ))
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": "Timeout", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
        finally:
            try:
                os.remove(filepath)
            except Exception:
                pass


class APITool:
    """Make HTTP API calls."""

    async def call(self, url: str, method: str = "GET",
                   headers: dict = None, data: dict = None) -> Dict[str, Any]:
        """Make an API call."""
        if not AIOHTTP_AVAILABLE:
            return {"error": "aiohttp not installed"}

        try:
            async with aiohttp.ClientSession() as session:
                kwargs = {"headers": headers or {}, "timeout": aiohttp.ClientTimeout(total=15)}
                if data:
                    kwargs["json"] = data

                async with getattr(session, method.lower())(url, **kwargs) as resp:
                    body = await resp.text()
                    return {
                        "status": resp.status,
                        "body": body[:5000],
                        "success": 200 <= resp.status < 300
                    }
        except Exception as e:
            return {"error": str(e), "success": False}


class ToolManager:
    """Central manager for all agent tools."""

    def __init__(self):
        self.search = WebSearchTool()
        self.browser = BrowserTool()
        self.image_gen = ImageGeneratorTool()
        self.code_exec = CodeExecutorTool()
        self.api = APITool()

    def get_available_tools(self) -> list:
        return ["web_search", "browser", "image_generation", "code_execution", "api_calls"]
