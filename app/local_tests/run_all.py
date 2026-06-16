from __future__ import annotations

import sys

from app.local_tests import test_canonical, test_chunking, test_pdf_extraction
from app.local_tests._util import OUTPUTS


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv

    print("\n##### canonical #####")
    test_canonical.main()
    print("\n##### chunking #####")
    test_chunking.main()
    print("\n##### pdf extraction #####")
    test_pdf_extraction.main(argv)

    print(f"\nAll reports written to {OUTPUTS}")


if __name__ == "__main__":
    main()
