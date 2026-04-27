import os
import re

def get_clients_root(base_dir):
    return os.path.join(base_dir, "clients")

def list_available_clients(clients_root):
    if os.path.isdir(clients_root):
        return [d for d in sorted(os.listdir(clients_root)) if os.path.isdir(os.path.join(clients_root, d))]
    return []

def find_client_folder_by_uploaded_file(clients_root, uploaded_file_name, uploaded_bytes):
    candidates = []
    for c in list_available_clients(clients_root):
        candidate = os.path.join(clients_root, c, uploaded_file_name)
        if os.path.exists(candidate):
            candidates.append(c)
    if not candidates:
        return None, "not_found", []
    elif len(candidates) == 1:
        return os.path.join(clients_root, candidates[0]), "unique", candidates
    else:
        matches = []
        for c in candidates:
            server_path = os.path.join(clients_root, c, uploaded_file_name)
            try:
                with open(server_path, "rb") as rf:
                    server_bytes = rf.read()
                if server_bytes == uploaded_bytes:
                    matches.append(c)
            except Exception:
                continue
        if len(matches) == 1:
            return os.path.join(clients_root, matches[0]), "unique_content", matches
        elif len(matches) > 1:
            return None, "multiple_content", matches
        else:
            return None, "no_content_match", candidates

def parse_ips_from_text(content):
    return [ip.strip() for ip in re.split(r"[,\n\r]+", content) if ip.strip()]
