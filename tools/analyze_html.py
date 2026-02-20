import json
import re
import sys


def find_cards_in_json(data, path=""):
    if isinstance(data, dict):
        if "className" in data:
            cls = str(data["className"])
            cls = " ".join(cls.split())
            if "rounded-2xl" in cls and "bg-neutralBg1" in cls:
                print(f"\n--- Potential Card Found at {path} ---")
                print(f"Class: {cls}")
                print(f"Content: {str(data)[:500]}")

        for k, v in data.items():
            find_cards_in_json(v, f"{path}.{k}")

    elif isinstance(data, list):
        for i, item in enumerate(data):
            find_cards_in_json(item, f"{path}[{i}]")
    elif isinstance(data, str):
        if data.strip().startswith("{") and data.strip().endswith("}"):
            try:
                nested = json.loads(data)
                find_cards_in_json(nested, path + "(parsed)")
            except Exception:
                pass


def analyze_html(file_path):
    print(f"Analyzing {file_path}...")
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    matches = re.findall(r"self\.__next_f\.push\(\[(.*?)\]\)", content, flags=re.DOTALL)

    print(f"Found {len(matches)} data pushes.")

    for i, match in enumerate(matches):
        try:
            parts = match.split(",", 1)
            if len(parts) < 2:
                continue

            payload_str = parts[1].strip()

            if payload_str.startswith('"') and payload_str.endswith('"'):
                try:
                    payload = json.loads(payload_str)
                    if isinstance(payload, str):
                        try:
                            if payload.strip().startswith("{") or payload.strip().startswith("["):
                                data = json.loads(payload)
                                find_cards_in_json(data, f"Block{i}")
                            else:
                                if "rounded-2xl" in payload and "bg-neutralBg1" in payload:
                                    print(f"\n--- Potential Card String in Block {i} ---")
                                    print(payload[:500])
                        except Exception:
                            if "rounded-2xl" in payload and "bg-neutralBg1" in payload:
                                print(f"\n--- Potential Card String in Block {i} ---")
                                print(payload[:500])
                    else:
                        find_cards_in_json(payload, f"Block{i}")
                except Exception:
                    pass
        except Exception:
            pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_html(sys.argv[1])
    else:
        print("Usage: python analyze_html.py <path_to_html>")
