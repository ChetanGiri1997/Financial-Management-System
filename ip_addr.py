import requests

def get_public_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json")
        response.raise_for_status()
        ip = response.json()["ip"]
        return ip
    except requests.RequestException as e:
        return f"Error: {e}"

if __name__ == "__main__":
    print("Public IP:", get_public_ip())
