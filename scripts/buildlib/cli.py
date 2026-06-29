import argparse

from .builder import build_pdf, build_site, clean


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=["site", "pdf", "all", "clean"])
    args = parser.parse_args()

    if args.target == "site":
        build_site()
        print("Built site")
    elif args.target == "pdf":
        build_pdf()
        print("Built site and PDF")
    elif args.target == "all":
        build_pdf()
        print("Built site and PDF")
    elif args.target == "clean":
        clean()
        print("Cleaned generated files")
