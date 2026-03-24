from agents.file_supervision_loop import FileSupervisionLoop


def test_file_supervision_loop_pending_and_reverification_cycle():
    loop = FileSupervisionLoop(max_attempts=2)

    assert loop.has_pending_corrections() is False
    assert loop.needs_reverification("app/page.tsx") is False

    first = loop.on_supervisor_needs_fix("app/page.tsx")
    assert first is True
    assert loop.has_pending_corrections() is True
    loop.reset_file("app/page.tsx")
    assert loop.needs_reverification("app/page.tsx") is True

    loop.on_supervisor_ok("app/page.tsx")
    assert loop.has_pending_corrections() is False
    assert loop.needs_reverification("app/page.tsx") is False


def test_file_supervision_loop_stops_injecting_after_max_attempts():
    loop = FileSupervisionLoop(max_attempts=2)

    assert loop.on_supervisor_needs_fix("app/page.tsx") is True
    loop.reset_file("app/page.tsx")
    assert loop.needs_reverification("app/page.tsx") is True

    # Deuxième signal => on consomme la dernière tentative restante.
    assert loop.on_supervisor_needs_fix("app/page.tsx") is True
    assert loop.needs_reverification("app/page.tsx") is False

    # Troisième signal => plus aucune injection, le fichier sort des pending.
    assert loop.on_supervisor_needs_fix("app/page.tsx") is False
    assert loop.has_pending_corrections() is False
    assert loop.needs_reverification("app/page.tsx") is False
