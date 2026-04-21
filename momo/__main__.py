"""支持 `python -m momo` 的模块入口。"""

from .app import main


if __name__ == "__main__":
    raise SystemExit(main())
