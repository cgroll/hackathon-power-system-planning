"""Download this repo's staged input data (PECD + MaStR extracts) and
unpack it into `data/input/`.

The archive is a zip of energy-data-hub's already-processed output
(https://github.com/cgroll/energy-data-hub -- see
`book/markdown/data_sources.md` for exactly what's in it and how it was
produced), shared via a Dropbox link so `dvc repro`/`make run` works right
after cloning -- no CDS or MaStR account needed. This is this repo's only
network-dependent stage; everything downstream reads from `data/input/`.

Re-download: delete `data/input/{pecd,mastr,regions}/`, or run
`dvc repro -f download_input_data` (the DVC stage uses `persist: true`, so
an existing download is otherwise left in place on every `dvc repro`).

If the link below ever breaks: re-zip energy-data-hub's
`data/{pecd,mastr,regions}/` subfolders (see this repo's git history for
the exact file list this was built from), re-share, and update
`INPUT_DATA_URL`.
"""

import tempfile
import urllib.request
import zipfile
from pathlib import Path

from hpsp.paths import ProjPaths

INPUT_DATA_URL = (
    "https://www.dropbox.com/scl/fi/u0irvww1j8qmgd7ldfmj6/"
    "hackathon-power-system-planning-input-data.zip"
    "?rlkey=4jvm9i3i7az0qm2gmzipkktg3&dl=1"
)

paths = ProjPaths()


def main() -> None:
    paths.ensure_directories()
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = Path(tmp_dir) / "input_data.zip"
        print(f"Downloading input data from {INPUT_DATA_URL} ...")
        urllib.request.urlretrieve(INPUT_DATA_URL, zip_path)
        size_mb = zip_path.stat().st_size / 1e6
        print(f"Downloaded {size_mb:.0f} MB, extracting to {paths.input_path} ...")
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(paths.input_path)
    print("Done.")


if __name__ == "__main__":
    main()
