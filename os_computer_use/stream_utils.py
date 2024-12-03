from playwright.async_api import async_playwright
import aiohttp
import asyncio
import subprocess
import os
import platform


async def get_stream(webpage_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(webpage_url)
        await page.wait_for_selector("mux-video")
        mux_video_element = await page.query_selector("mux-video")
        video_url = (
            await mux_video_element.get_attribute("src") if mux_video_element else None
        )
        await browser.close()
        return video_url


def start_ffmpeg(m3u8_url, output_filename):
    if os.path.exists(output_filename):
        os.remove(output_filename)
    command = ["ffmpeg", "-i", m3u8_url, "-c", "copy", output_filename]
    process = subprocess.Popen(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return process


def open_in_quicktime(url):
    if platform.system() == "Darwin":  # macOS
        try:
            os.system(f'open -a "QuickTime Player" "{url}"')
        except Exception as e:
            print(f"Error opening in QuickTime: {e}")
    else:
        print("This script is only for macOS.")


async def check_stream_status(session, url):
    try:
        async with session.get(url) as response:
            data = await response.text()
            if "#EXT-X-STREAM-INF" in data:
                print("Stream is active and ready!")
                return True
            else:
                print("Waiting for stream to start...")
                return False
    except Exception as e:
        print(f"Error: {e}")
        return False


async def poll_stream_until_ready(url, delay=3):
    async with aiohttp.ClientSession() as session:
        while True:
            is_ready = await check_stream_status(session, url)
            if is_ready:
                break
            await asyncio.sleep(delay)
