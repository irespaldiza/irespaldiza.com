import os
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .paths import ROOT


def find_chrome():
    configured = os.environ.get("CHROME")
    if configured:
        return configured

    mac_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if mac_chrome.exists():
        return str(mac_chrome)

    for candidate in ("google-chrome", "chromium"):
        path = shutil.which(candidate)
        if path:
            return path

    raise RuntimeError("Chrome or Chromium is required to generate PDFs from HTML.")


def html_to_pdf(input_html, output_pdf):
    chrome = find_chrome()
    input_path = input_html.resolve()
    output_path = output_pdf.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_pdf = output_path.with_name(f"{output_path.name}.tmp.{os.getpid()}")

    if tmp_pdf.exists():
        tmp_pdf.unlink()

    with tempfile.TemporaryDirectory(prefix="resume-chrome.") as profile_dir:
        chrome_args = shlex.split(os.environ.get("CHROME_EXTRA_ARGS", ""))
        chrome_stderr = Path(profile_dir) / "chrome-stderr.log"
        with chrome_stderr.open("wb") as stderr_handle:
            process = subprocess.Popen(
                [
                    chrome,
                    "--headless",
                    "--disable-gpu",
                    "--disable-background-networking",
                    "--disable-default-apps",
                    "--disable-extensions",
                    "--disable-sync",
                    "--disable-translate",
                    "--metrics-recording-only",
                    "--no-default-browser-check",
                    "--no-first-run",
                    f"--user-data-dir={profile_dir}",
                    "--no-pdf-header-footer",
                    f"--print-to-pdf={tmp_pdf}",
                    *chrome_args,
                    f"file://{input_path}",
                ],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=stderr_handle,
            )

            for _ in range(180):
                if tmp_pdf.exists() and tmp_pdf.stat().st_size > 0:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                    tmp_pdf.replace(output_path)
                    mark_pdf_links_new_window(output_path)
                    return

                if process.poll() is not None:
                    break

                time.sleep(1)

            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

        stderr_output = chrome_stderr.read_text(encoding="utf-8", errors="replace").strip()

    if stderr_output:
        tail = "\n".join(stderr_output.splitlines()[-10:])
        raise RuntimeError(
            f"Failed to generate PDF: {output_path}\n"
            f"Chrome stderr:\n{tail}"
        )

    raise RuntimeError(f"Failed to generate PDF: {output_path}")


def mark_pdf_links_new_window(pdf_path):
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import BooleanObject, NameObject

    reader = PdfReader(pdf_path)
    changed = False

    for page in reader.pages:
        for annotation_ref in page.get("/Annots", []):
            annotation = annotation_ref.get_object()
            if annotation.get("/Subtype") != "/Link":
                continue

            action = annotation.get("/A")
            if action is None:
                continue
            action = action.get_object()
            if action.get("/S") != "/URI":
                continue
            action[NameObject("/NewWindow")] = BooleanObject(True)
            changed = True

    if not changed:
        return

    rewritten_path = pdf_path.with_name(f"{pdf_path.name}.links.{os.getpid()}")
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    with rewritten_path.open("wb") as output:
        writer.write(output)
    rewritten_path.replace(pdf_path)
