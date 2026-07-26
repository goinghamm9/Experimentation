"""Local annotation server — stdlib only, so the package stays dependency-free.

Binds to localhost by default. The corpus reaching this server is post-gate
(consented, minimised, redacted), but it is still participant data, so the server
refuses to bind to a public interface without an explicit acknowledgement.
"""

from __future__ import annotations

import hashlib
import json
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from ..rigor import probability_sample
from ..schema import Corpus
from .store import Annotation, GoldStore
from .ui import render_page


@dataclass
class AnnotationSession:
    corpus: Corpus
    codes: list[dict[str, str]]
    store: GoldStore
    annotator: str
    sample_size: int
    seed: str = "gold"

    def unit_ids(self) -> list[str]:
        """The probability sample — reproducible for a given seed and corpus."""
        return probability_sample(
            [o.id for o in self.corpus.observations], self.sample_size, self.seed
        )

    def codebook_version(self) -> str:
        """Content hash of the codebook, so annotations are tied to the rubric used.

        A changed codebook invalidates comparability — this is what makes that
        detectable instead of silent.
        """
        blob = json.dumps(sorted(c["label"] for c in self.codes), sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:12]

    def units_payload(self) -> list[dict]:
        wanted = set(self.unit_ids())
        order = {u: i for i, u in enumerate(self.unit_ids())}
        out = []
        for o in self.corpus.observations:
            if o.id not in wanted:
                continue
            payload = {k: v for k, v in o.payload.items() if k != "event"} if o.payload else {}
            out.append({
                "id": o.id,
                "text": o.text or "",
                "source": o.source,
                "kind": o.kind.value,
                "timestamp": o.timestamp.strftime("%Y-%m-%d %H:%M"),
                # NOTE: no machine label is included, by design. Blind coding.
                "payload": payload,
            })
        out.sort(key=lambda u: order.get(u["id"], 0))
        return out


def _handler_factory(session: AnnotationSession):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # keep the console quiet
            pass

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Frame-Options", "DENY")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path not in ("/", "/index.html"):
                self._send(404, b"not found", "text/plain")
                return
            units = session.units_payload()
            done = {
                uid: a.label
                for uid, a in session.store.latest_by_unit(session.annotator).items()
            }
            page = render_page(
                study_title=session.corpus.study.title,
                annotator=session.annotator,
                units_json=json.dumps(units),
                codes_json=json.dumps(session.codes),
                annotator_json=json.dumps(session.annotator),
                codebook_version_json=json.dumps(session.codebook_version()),
                done_json=json.dumps(done),
            )
            self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")

        def do_POST(self) -> None:
            if self.path != "/annotate":
                self._send(404, b"not found", "text/plain")
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length))
                session.store.add(Annotation(
                    unit_id=str(data["unit_id"]),
                    label=data.get("label"),
                    annotator=str(data.get("annotator", session.annotator)),
                    codebook_version=str(data.get("codebook_version", "")),
                    seconds_on_task=float(data.get("seconds_on_task", 0.0)),
                    note=str(data.get("note", "")),
                ))
                self._send(200, b'{"ok":true}', "application/json")
            except Exception as exc:  # noqa: BLE001 — report, never crash mid-session
                self._send(400, json.dumps({"error": str(exc)}).encode(), "application/json")

    return Handler


def serve(
    session: AnnotationSession,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
    allow_public: bool = False,
) -> None:
    """Run the annotation UI until interrupted."""
    if host not in ("127.0.0.1", "localhost", "::1") and not allow_public:
        raise ValueError(
            f"Refusing to bind to {host}: the corpus contains participant data. "
            "Pass allow_public=True only behind an authenticated proxy."
        )

    n = len(session.unit_ids())
    already = len(session.store.completed_units(session.annotator))
    url = f"http://{host}:{port}/"
    print(f"Gold coding: {already}/{n} units already coded by '{session.annotator}'")
    print(f"Codebook version {session.codebook_version()} · writing to {session.store.path}")
    print(f"Open {url}  (Ctrl-C to stop)")

    httpd = HTTPServer((host, port), _handler_factory(session))
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()


def build_session(
    corpus: Corpus,
    codebook: dict[str, list[str]] | None,
    gold_path: str | Path,
    annotator: str,
    sample_size: int,
    seed: str = "gold",
) -> AnnotationSession:
    """Assemble a session from a post-gate corpus and the study's codebook."""
    labels = sorted(codebook) if codebook else []
    codes = [
        {"label": label, "definition": ", ".join(codebook[label][:4]) if codebook else ""}
        for label in labels
    ]
    return AnnotationSession(
        corpus=corpus,
        codes=codes,
        store=GoldStore(gold_path),
        annotator=annotator,
        sample_size=sample_size,
        seed=seed,
    )
