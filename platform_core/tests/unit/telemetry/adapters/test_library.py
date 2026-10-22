import io
import threading

from platform_core.telemetry.adapters.library import LibraryAdapter


def test_library_adapter_emits_without_spawning_a_background_thread(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER", raising=False)
    stream = io.StringIO()
    adapter = LibraryAdapter(app_id="snack-sdk", team="platform-eng", environment="dev", stream=stream)

    threads_before = threading.active_count()
    with adapter.start_span("event"):
        adapter.log("info", "event emitted")
    threads_after = threading.active_count()

    assert threads_after == threads_before
