# Copyright 2021 eprbell
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil
import unittest
from pathlib import Path
from subprocess import run

from ods_diff import ods_diff

ROOT_PATH: Path = Path(os.path.dirname(__file__)).parent.absolute()

CONFIG_PATH: Path = ROOT_PATH / Path("config")
INPUT_PATH: Path = ROOT_PATH / Path("input")
GOLDEN_PATH: Path = INPUT_PATH / Path("golden")
LOG_PATH: Path = ROOT_PATH / Path("log")
OUTPUT_PATH: Path = ROOT_PATH / Path("output")


class TestODSOutputDiff(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Generate output to compare with golden files
        shutil.rmtree(LOG_PATH, ignore_errors=True)
        shutil.rmtree(OUTPUT_PATH, ignore_errors=True)
        run(
            ["rp2", "-o", str(OUTPUT_PATH), "-p", "test_data_", str(CONFIG_PATH / Path("test_data.config")), str(INPUT_PATH / Path("test_data.ods"))],
            check=True,
        )
        run(
            [
                "rp2",
                "-o",
                str(OUTPUT_PATH),
                "-p",
                "crypto_example_",
                str(CONFIG_PATH / Path("crypto_example.config")),
                str(INPUT_PATH / Path("crypto_example.ods")),
            ],
            check=True,
        )

    def setUp(self) -> None:
        self.maxDiff = None  # pylint: disable=C0103

    def test_data_tax_report_plugin(self) -> None:
        diff: str = ods_diff(
            GOLDEN_PATH / Path("test_data_rp2_report_golden.ods"),
            OUTPUT_PATH / Path("test_data_rp2_report.ods"),
        )
        self.assertFalse(diff, msg=diff)

    def test_data_mock_8949_plugin(self) -> None:
        diff: str = ods_diff(
            GOLDEN_PATH / Path("test_data_mock_8949_us_golden.ods"),
            OUTPUT_PATH / Path("test_data_mock_8949_us.ods"),
        )
        self.assertFalse(diff, msg=diff)

    def test_crypto_example_tax_report_plugin(self) -> None:
        diff: str = ods_diff(
            GOLDEN_PATH / Path("crypto_example_rp2_report_golden.ods"),
            OUTPUT_PATH / Path("crypto_example_rp2_report.ods"),
        )
        self.assertFalse(diff, msg=diff)

    def test_crypto_example_mock_8949_plugin(self) -> None:
        diff: str = ods_diff(
            GOLDEN_PATH / Path("crypto_example_mock_8949_us_golden.ods"),
            OUTPUT_PATH / Path("crypto_example_mock_8949_us.ods"),
        )
        self.assertFalse(diff, msg=diff)


if __name__ == "__main__":
    unittest.main()
