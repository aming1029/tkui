"""Convenience launcher: python demo.py [--style web|win11|auto|ask]."""
import argparse

from tkui.demo import run_demo


def main():
    parser = argparse.ArgumentParser(description="TkUI 组件画廊")
    parser.add_argument("--style", "-s", default=None,
                        help="web / win11 / auto / ask")
    parser.add_argument("--page", default=None, help="初始页面 key")
    parser.add_argument("--choose", action="store_true", help="先弹出风格选择")
    args = parser.parse_args()
    return run_demo(style=args.style, page=args.page, choose=args.choose)


if __name__ == "__main__":
    main()
