from pathlib import Path

from scripts.make_install import write_windows_launcher


def test_write_windows_launcher_uses_only_user_args(tmp_path: Path) -> None:
    launcher_path = tmp_path / "userdic-py.cmd"
    write_windows_launcher(launcher_path, "py")

    content = launcher_path.read_text(encoding="utf-8")
    assert "run(sys.argv[1:])" in content
    assert "os.environ['SCRIPT_DIR']" in content
    assert "\"%SCRIPT_DIR%\"" not in content
