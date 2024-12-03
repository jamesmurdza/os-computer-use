from e2b_desktop import Sandbox
from os_computer_use.sandbox_agent import SandboxAgent
from os_computer_use.llm import qwen
from os_computer_use.stream_utils import (
    get_stream,
    start_ffmpeg,
    open_in_quicktime,
    poll_stream_until_ready,
)

import asyncio


async def start():
    sandbox = Sandbox(video_stream=True)
    webpage_url = sandbox.get_video_stream_url()
    video_url = await get_stream(webpage_url)

    agent = SandboxAgent(qwen, sandbox)

    lag_start_time = asyncio.get_event_loop().time()
    await poll_stream_until_ready(video_url)
    lag_time = asyncio.get_event_loop().time() - lag_start_time

    ffmpeg_process = start_ffmpeg(video_url, "stream.mp4")
    open_in_quicktime(video_url)

    agent.run(
        "Do the following: 1) Open Firefox 2) Use run_command to sleep for two seconds 3) Click on the URL bar 4) Type a URL."
    )

    sandbox.kill()

    await asyncio.sleep(lag_time)
    ffmpeg_process.terminate()
    ffmpeg_process.wait()


def main():
    asyncio.run(start())
