"""Approvals bind a human, or they are only a name.

`README.md` carried this as a stated limitation until 0.1.2: an agent could run
`approve_edge.py --by product-owner` exactly as a person could, so `approved` meant "someone
took accountability under this name". `validate_approvals.py` closes it by verifying the one
thing the README named as a real anchor — a signed commit, checked against a trust root the
project keeps in version control.

The signature tests here build a real git repository and make a real signature. A mocked
`git verify-commit` would assert that the mock was called, which is the check-that-cannot-fail
this project exists to reject.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess

import pytest

from conftest import assert_fails, failing


# -- the matrix ------------------------------------------------------------------------


def test_the_good_fixture_passes(project):
    """The fixture names its approvers and its approvals resolve to them."""
    verdict = project.run("validate_approvals")
    assert verdict.status == "PASS", f"failing: {sorted(failing(verdict))}"


def test_a_blank_approval_matrix_fails(project):
    """The shipped template blank, which is the state every new project starts in.

    The template says why this matters in its own words: "If nobody is named here, anyone can
    override anything and the gate is decorative." APV-000 is that sentence, checked.
    """
    matrix = project.root / ".specify/governance/approval-matrix.md"
    matrix.write_text(
        matrix.read_text()
        .replace("| product-owner |", "| |")
        .replace("| architect |", "| |")
        .replace("| security-team |", "| |")
        .replace("| release-owner |", "| |")
        .replace("| iteration-owner |", "| |")
        .replace("| qa-lead |", "| |")
        .replace("| backend-lead |", "| |")
    )
    assert_fails(project.run("validate_approvals"), "APV-000")


def test_an_approver_the_matrix_does_not_name_fails(project):
    """The specific escape this closes: approving under a name nobody agreed to."""
    project.artifact("TC-AUTH-0031")(
        lambda a: a["approvals"].__setitem__(0, {"by": "some-agent", "at": "2026-09-10T09:00:00Z"})
    )
    verdict = project.run("validate_approvals")
    assert_fails(verdict, "APV-003")
    assert any("some-agent" in item for check in verdict.checks for item in check.evidence)


def test_prose_in_the_matrix_is_not_read_as_an_approver(project):
    """The parser reads the 'who' column, not every cell.

    Scraping the whole table would admit "Business scope" and "security review" as approvers,
    which would make APV-000 pass on a matrix that names nobody — the precise failure the
    check exists to catch, reintroduced by its own parser.
    """
    import validate_approvals

    names = validate_approvals.named_humans(project.root)
    assert "Business scope" not in names
    assert "security review" not in names
    assert "product-owner" in names


def test_a_body_cell_containing_the_word_approvals_is_not_a_header(project):
    """A regression guard with a real cause.

    The matrix has a row ending "…status → `BASELINED`, with `approvals`". A header detector
    that matched on the word rather than on the separator row beneath it re-anchored the
    column there and read every later row from the wrong cell.
    """
    import validate_approvals

    names = validate_approvals.named_humans(project.root)
    assert not any("approvals" in name for name in names), sorted(names)
    assert not any(name.startswith(("REQ-", "BUS-OBJ-", "CONTRACT-")) for name in names)


# -- the witness floor -----------------------------------------------------------------


def test_a_claimed_approval_warns_but_does_not_fail(project):
    """APV-004 warns by default, so an upgrading project is told without being broken.

    Defaulting the floor to BASELINED would fail the first audit of every project carrying
    approvals recorded before `commit` was checked. The warning makes the gap visible; raising
    the floor is what makes it consequential.
    """
    verdict = project.run("validate_approvals")
    warned = {c.id for c in verdict.checks if c.status == "WARN"}
    assert "APV-004" in warned
    assert verdict.status == "PASS"


def test_raising_the_floor_makes_claimed_approvals_fail(project):
    """The ratchet. Nothing changes but the config, and the same data now fails."""
    project.config(lambda c: c.setdefault("approvals", {}).__setitem__(
        "require_witness_at_or_above", "BASELINED"))
    verdict = project.run("validate_approvals")
    assert_fails(verdict, "APV-005")


def test_the_floor_only_binds_states_at_or_above_it(project):
    """A DRAFT artifact's approval is not held to the BASELINED floor."""
    project.config(lambda c: c.setdefault("approvals", {}).__setitem__(
        "require_witness_at_or_above", "ACCEPTED"))
    verdict = project.run("validate_approvals")
    # Every fixture approval sits on a VERIFIED artifact, below ACCEPTED.
    assert "APV-005" not in failing(verdict)


# -- signatures, against a real repository ---------------------------------------------


def _git(root: pathlib.Path, *args: str, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True, **kwargs)


@pytest.fixture
def signing_project(project, tmp_path):
    """The fixture as a real git repository, with a real ssh signing key.

    Skips rather than fakes when the toolchain is absent. A skip says "not checked here"; a
    mock would say "checked" about something that never ran.
    """
    if shutil.which("git") is None or shutil.which("ssh-keygen") is None:
        pytest.skip("git and ssh-keygen are needed to make a real signature")

    key = tmp_path / "signing-key"
    made = subprocess.run(
        ["ssh-keygen", "-t", "ed25519", "-N", "", "-C", "approver@example.org", "-f", str(key)],
        capture_output=True, text=True,
    )
    if made.returncode != 0:
        pytest.skip(f"ssh-keygen unavailable: {made.stderr.strip()}")

    root = project.root
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "Approver")
    _git(root, "config", "user.email", "approver@example.org")
    _git(root, "config", "gpg.format", "ssh")
    _git(root, "config", "user.signingkey", str(key))
    _git(root, "add", "-A")

    signers = root / ".specify/governance/allowed-signers"
    signers.write_text(f"approver@example.org {key.with_suffix('.pub').read_text().strip()}\n")
    _git(root, "add", "-A")

    signed = _git(root, "commit", "-q", "-S", "-m", "Approve the authentication requirement")
    if signed.returncode != 0:
        pytest.skip(f"this git cannot make an ssh-signed commit: {signed.stderr.strip()}")

    project.signed_sha = _git(root, "rev-parse", "HEAD").stdout.strip()
    project.signing_key = key
    return project


def test_a_signed_commit_witnesses_an_approval(signing_project):
    """The whole point of the release: an approval that git can check."""
    signing_project.artifact("TC-AUTH-0031")(
        lambda a: a["approvals"].__setitem__(0, {
            "by": "qa-lead",
            "at": "2026-09-10T09:00:00Z",
            "commit": signing_project.signed_sha,
        })
    )
    verdict = signing_project.run("validate_approvals")
    assert verdict.status == "PASS", f"failing: {sorted(failing(verdict))}"
    assert verdict.metrics["witnessed"] == 1


def test_an_unsigned_commit_does_not_witness_an_approval(signing_project):
    """An approval pointing at a real but unsigned commit is still only a claim."""
    unsigned = _git(signing_project.root, "commit", "-q", "--allow-empty", "--no-gpg-sign",
                    "-m", "An ordinary commit")
    assert unsigned.returncode == 0
    sha = _git(signing_project.root, "rev-parse", "HEAD").stdout.strip()

    signing_project.artifact("TC-AUTH-0031")(
        lambda a: a["approvals"].__setitem__(0, {
            "by": "qa-lead", "at": "2026-09-10T09:00:00Z", "commit": sha,
        })
    )
    assert_fails(signing_project.run("validate_approvals"), "APV-002")


def test_a_commit_that_does_not_exist_fails(signing_project):
    """A plausible-looking sha that is not in this repository."""
    signing_project.artifact("TC-AUTH-0031")(
        lambda a: a["approvals"].__setitem__(0, {
            "by": "qa-lead", "at": "2026-09-10T09:00:00Z",
            "commit": "0123456789abcdef0123456789abcdef01234567",
        })
    )
    assert_fails(signing_project.run("validate_approvals"), "APV-001")


def test_a_signature_from_a_key_the_project_does_not_trust_fails(signing_project, tmp_path):
    """The trust root decides, not the presence of a signature.

    A commit signed by a key nobody listed verifies as "signed" to git and must not verify as
    "approved" here — otherwise anyone who can commit can approve.
    """
    signers = signing_project.root / ".specify/governance/allowed-signers"
    signers.write_text("someone-else@example.org ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDummyKey\n")

    signing_project.artifact("TC-AUTH-0031")(
        lambda a: a["approvals"].__setitem__(0, {
            "by": "qa-lead", "at": "2026-09-10T09:00:00Z",
            "commit": signing_project.signed_sha,
        })
    )
    assert_fails(signing_project.run("validate_approvals"), "APV-002")


def test_a_missing_trust_root_fails_rather_than_passing_silently(signing_project):
    """No allowed-signers file means no signature can be trusted, and it must say so."""
    (signing_project.root / ".specify/governance/allowed-signers").unlink()
    signing_project.artifact("TC-AUTH-0031")(
        lambda a: a["approvals"].__setitem__(0, {
            "by": "qa-lead", "at": "2026-09-10T09:00:00Z",
            "commit": signing_project.signed_sha,
        })
    )
    verdict = signing_project.run("validate_approvals")
    assert_fails(verdict, "APV-002")
    assert any("trust root" in item for check in verdict.checks for item in check.evidence)


# -- the exit contract -----------------------------------------------------------------


def test_a_declared_commit_outside_a_git_repository_exits_2(project):
    """Could not evaluate, not "the approvals are bad".

    The fixture is copied to a temp directory with no `.git`. An approval declaring a commit
    there cannot be checked, and reporting that as a governance failure would send someone
    looking for a defect in their data rather than in their environment.
    """
    project.artifact("TC-AUTH-0031")(
        lambda a: a["approvals"].__setitem__(0, {
            "by": "qa-lead", "at": "2026-09-10T09:00:00Z",
            "commit": "0123456789abcdef0123456789abcdef01234567",
        })
    )
    assert project.script_rc("validate_approvals.py", "--json") == 2


def test_claimed_approvals_need_no_git_at_all(project):
    """A project that never declares a commit never invokes git, so it cannot exit 2."""
    assert project.script_rc("validate_approvals.py", "--json") == 0
