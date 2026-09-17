import hashlib
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

import certifi
import requests

CST_URL = "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=199983"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
USER_AGENT = "Mozilla/5.0 (compatible; normativa-laboral-rag/0.1)"

# funcionpublica.gov.co envía el intermedio equivocado (Sectigo RSA Domain
# Validation en vez de Organization Validation, que es el que realmente firmó
# su certificado), por lo que la cadena nunca cierra con el bundle de certifi
# solo. Este es el intermedio correcto, descargado de crt.sectigo.com
# (sha256 72:A3:4A:C2:B4:24:AE:D3:F6:B0:B0:47:55:B8:8C:C0:27:DC:CC:80:6F:DD:B2:2B:4C:D7:C4:77:73:97:3E:C0).
MISSING_INTERMEDIATE = Path(__file__).resolve().parent.parent / "certs" / "sectigo_rsa_ov_intermediate.pem"


@lru_cache(maxsize=1)
def _ca_bundle_path() -> str:
    # Cacheado: sin esto, cada llamada dejaba un .pem huérfano en /tmp
    # (NamedTemporaryFile con delete=False nunca se limpiaba solo).
    combined = Path(certifi.where()).read_bytes() + b"\n" + MISSING_INTERMEDIATE.read_bytes()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
    tmp.write(combined)
    tmp.close()
    return tmp.name


def fetch(url: str, out_path: Path) -> Path:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30, verify=_ca_bundle_path())
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
