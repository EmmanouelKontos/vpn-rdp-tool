import requests
import platform
import os
import sys

GITHUB_REPO = "EmmanouelKontos/vpn-rdp-tool"  # Replace with your actual GitHub username and repo name
CURRENT_VERSION = "v1.0.7"  # This should be updated with each release

def get_latest_release():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching latest release: {e}")
        return None

def check_for_updates():
    latest_release = get_latest_release()
    if latest_release:
        latest_version = latest_release['tag_name']
        if latest_version > CURRENT_VERSION:
            return True, latest_version, latest_release['assets']
    return False, None, None

def download_asset(asset_url, download_path, progress_callback=None):
    try:
        response = requests.get(asset_url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded_size += len(chunk)
                if progress_callback:
                    progress_callback(downloaded_size, total_size)
        return True, ""
    except requests.exceptions.RequestException as e:
        return False, str(e)

def get_appropriate_asset(assets):
    system = platform.system()
    if system == "Windows":
        for asset in assets:
            if asset['name'].endswith(".exe"):
                return asset
    elif system == "Linux":
        for asset in assets:
            # Assuming Linux executable has no extension or a .run/.bin extension
            if "UniversalVPNTool" in asset['name'] and not asset['name'].endswith(".exe"):
                return asset
    return None

# Example usage (for testing purposes)
if __name__ == "__main__":
    update_available, latest_version, assets = check_for_updates()
    if update_available:
        print(f"Update available! Latest version: {latest_version}")
        asset_to_download = get_appropriate_asset(assets)
        if asset_to_download:
            print(f"Downloading {asset_to_download['name']}...")
            download_success, error_message = download_asset(asset_to_download['browser_download_url'], asset_to_download['name'])
            if download_success:
                print("Download complete!")
            else:
                print(f"Download failed: {error_message}")
        else:
            print("No appropriate asset found for this OS.")
    else:
        print("No updates available.")
