import json
import re
from pathlib import Path


def _load_authorid_guard_pattern() -> str:
    cfg_path = (
        Path(__file__).resolve().parents[1]
        / "config"
        / "stacks"
        / "nextjs-clerk-prisma.json"
    )
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    guards = cfg.get("content_guards", [])
    guard = next(g for g in guards if g.get("id") == "authorid_requires_userid_guard")
    patterns = guard.get("requires_regex_all", [])
    assert patterns, "requires_regex_all manquant pour authorid_requires_userid_guard"
    return str(patterns[0])


def test_authorid_guard_requires_negated_userid_check():
    pattern = _load_authorid_guard_pattern()
    rx = re.compile(pattern, re.MULTILINE)

    bad_code = """
export async function POST() {
  const { userId } = await auth()
  if (userId) return NextResponse.json({ ok: true })
  await prisma.post.create({ data: { authorId: userId } })
}
"""
    good_code = """
export async function POST() {
  const { userId } = await auth()
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  await prisma.post.create({ data: { authorId: userId } })
}
"""

    assert not rx.search(bad_code), "if(userId) ne doit PAS satisfaire le guard"
    assert rx.search(good_code), "if(!userId) doit satisfaire le guard"
