"""Run every local test runner in sequence.

    python -m app.local_tests.run_all              # canonical + chunking (+ PDF if one is found)
    python -m app.local_tests.run_all file.pdf     # forward a PDF to the extraction runner

Each runner writes its own ``outputs/<name>_result.txt``; this just chains them
so one command refreshes all reports.
"""

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
