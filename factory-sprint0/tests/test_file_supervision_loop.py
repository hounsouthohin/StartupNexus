from agents.file_supervision_loop import FileSupervisionLoop


def test_on_supervisor_needs_fix_decrements_attempts():
    loop = FileSupervisionLoop(max_attempts=2)
    path = "app/page.tsx"

    assert loop.on_supervisor_needs_fix(path) is True
    assert loop._pending[path] == 1
    assert loop.on_supervisor_needs_fix(path) is True
    assert loop._pending[path] == 0

def test_on_supervisor_ok_clears_pending():
    loop = FileSupervisionLoop(max_attempts=2)
    path = "app/page.tsx"
    loop.on_supervisor_needs_fix(path)
    assert loop.has_pending_corrections() is True

    loop.on_supervisor_ok(path)

    assert loop.has_pending_corrections() is False
    assert path not in loop.pending_paths()


def test_reset_file_arms_reverify_when_pending():
    loop = FileSupervisionLoop(max_attempts=2)
    path = "app/page.tsx"

    loop.on_supervisor_needs_fix(path)
    loop.reset_file(path)

    assert loop.needs_reverification(path) is True
    assert loop.needs_reverification(path) is False


def test_reset_file_no_action_on_new_file():
    loop = FileSupervisionLoop(max_attempts=2)
    path = "app/new.tsx"

    loop.reset_file(path)

    assert loop.has_pending_corrections() is False
    assert loop.needs_reverification(path) is False


def test_max_attempts_validates_best_effort():
    loop = FileSupervisionLoop(max_attempts=2)
    path = "app/page.tsx"

    assert loop.on_supervisor_needs_fix(path) is True
    assert loop.on_supervisor_needs_fix(path) is True
    # troisième fois: max atteint -> False + sortie de pending
    assert loop.on_supervisor_needs_fix(path) is False
    assert loop.has_pending_corrections() is False
