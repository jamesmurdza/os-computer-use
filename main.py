from e2b_desktop import Sandbox as SandboxBase
from os_computer_use.sandbox_agent import SandboxAgent
from os_computer_use.llm import qwen
import asyncio
import os
import signal


class Sandbox(SandboxBase):

    def start_stream(self):
        command = "ffmpeg -f x11grab -s 1024x768 -framerate 30 -i :99 -vcodec libx264 -preset ultrafast -tune zerolatency -f mpegts -listen 1 http://localhost:8080"
        process = self.commands.run(
            command,
            background=True,
        )
        return f"https://{self.get_host(8080)}", process


async def start():
    sandbox = Sandbox()

    print("Starting the display server...")
    stream_url, stream_process = sandbox.start_stream()
    await asyncio.sleep(2.5)

    print("Starting the display client...")
    process = await asyncio.create_subprocess_shell(
        f"ffmpeg -reconnect 1 -i {stream_url} -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k -f mpegts -loglevel quiet - | tee output.ts | ffplay -autoexit -i -loglevel quiet -",
        preexec_fn=os.setsid,
    )

    print("Running the agent...")
    agent = SandboxAgent(qwen, sandbox)

    agent.run(
        "Do the following: 1) Open Firefox 2) Use run_command to sleep for two seconds 3) Click on the URL bar 4) Type a URL."
    )

    print("Stopping the display client...")
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except ProcessLookupError:
        pass
    await process.wait()
    print("Stopping the display server...")
    stream_process.kill()
    print("Stopping the sandbox...")
    sandbox.kill()

    print("Saving the stream as mp4...")
    if os.path.exists("output.mp4"):
        os.remove("output.mp4")
    process = await asyncio.create_subprocess_shell(
        "ffmpeg -i output.ts -c:v copy -c:a copy -loglevel quiet output.mp4"
    )
    await process.wait()
    if process.returncode == 0:
        print("Stream saved successfully as mp4.")
    else:
        print("Failed to save the stream as mp4.")


def main():
    asyncio.run(start())
