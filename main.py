import argparse
import sys

from recognizer import *


def main():
    parser = argparse.ArgumentParser(description='語音轉文字CLI工具，使用AZURE語音服務')
    parser.add_argument(
        '-v', '--voice', required=False, action="store_true", help='從麥克風辨識(一次性)')
    parser.add_argument(
        '-f', '--file', required=False, type=str, help='從語音檔辨識')
    if len(sys.argv) == 1:
        return parser.print_help(sys.stderr)

    args = parser.parse_args()

    if args.voice:
        translation_once_from_mic()
    elif args.file:
        file_path = str(args.file).strip()
        translation_once_from_file(file_path)


if __name__ == "__main__":
    main()
