from pathlib import Path

from django.http import HttpResponse


_SERVICE_WORKER = Path(__file__).parent / "static" / "core" / "pwa" / "service-worker.js"


def service_worker(request):
    response = HttpResponse(
        _SERVICE_WORKER.read_text(encoding="utf-8"),
        content_type="application/javascript; charset=utf-8",
    )
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response
