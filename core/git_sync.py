import subprocess
import config


class GitService:
    @staticmethod
    def _exec(args: list[str]) -> tuple[bool, str]:
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=config.BASE_DIR,
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            if res.returncode == 0:
                return True, res.stdout.strip()
            return False, res.stderr.strip()
        except Exception as e:
            return False, str(e)

    @classmethod
    def status(cls) -> str:
        ok, out = cls._exec(["status", "-s"])
        return out if ok else f"Error: {out}"

    @classmethod
    def diff(cls, rel_path: str = None) -> str:
        has_head, _ = cls._exec(["rev-parse", "--verify", "HEAD"])

        if has_head:
            args = ["diff", "HEAD"]
        else:
            args = ["diff", "--cached"]

        if rel_path:
            args.extend(["--", rel_path])

        ok, out = cls._exec(args)

        if not out:
            unstaged_args = ["diff"]
            if rel_path:
                unstaged_args.extend(["--", rel_path])
            ok, out = cls._exec(unstaged_args)

        if not ok:
            return f"Diff error: {out}"
        return out if out else "Working tree clean."