import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_installed_console_entrypoints_smoke():
    """Regression guard: editable install must expose working console scripts."""
    script = ROOT / "scripts" / "validate_main_flow.sh"
    assert script.exists(), f"Missing validation script: {script}"

    result = subprocess.run(
        ["bash", str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=240,
    )

    assert "OK: main Hermes context flow validated in isolated temp environment." in result.stdout
