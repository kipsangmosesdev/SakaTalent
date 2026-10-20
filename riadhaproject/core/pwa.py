from pathlib import Path

from django.http import Http404, HttpResponse


_PWA_DIR = Path(__file__).parent / "static" / "core" / "pwa"
_PWA_ASSETS = {
    "icon-192.png": "image/png",
    "icon-512.png": "image/png",
    "icon-maskable-512.png": "image/png",
    "icon-maskable.svg": "image/svg+xml",
    "offline.html": "text/html; charset=utf-8",
}


def manifest(request):
    response = HttpResponse(
        (_PWA_DIR / "manifest.webmanifest").read_text(encoding="utf-8"),
        content_type="application/manifest+json; charset=utf-8",
    )
    response["Cache-Control"] = "no-cache"
    return response


def pwa_asset(request, asset_name):
    content_type = _PWA_ASSETS.get(asset_name)
    if content_type is None:
        raise Http404

    response = HttpResponse((_PWA_DIR / asset_name).read_bytes(), content_type=content_type)
    response["Cache-Control"] = "public, max-age=3600"
    return response


def service_worker(request):
    response = HttpResponse(
        (_PWA_DIR / "service-worker.js").read_text(encoding="utf-8"),
        content_type="application/javascript; charset=utf-8",
    )
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response
