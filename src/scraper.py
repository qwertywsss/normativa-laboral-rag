import hashlib
import sys
from pathlib import Path

import requests

CST_URL = "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=199983"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
USER_AGENT = "Mozilla/5.0 (compatible; normativa-laboral-rag/0.1)"


def fetch(url: str, out_path: Path) -> Path:
    # funcionpublica.gov.co sirve una cadena de certificados incompleta; sin esto
    # el TLS handshake falla con "unable to verify the first certificate".
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30, verify=False)
    response.raise_for_status()
    out_path.write_bytes(response.content)
    return out_path


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / "decreto_2663_1950.html"
    fetch(CST_URL, out_path)
    print(f"Guardado en {out_path}")
    print(f"sha256: {sha256_of(out_path)}")
    sys.exit(0)
