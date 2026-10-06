"""Puertas de CLI con BRR sintético; no versiona assets del juego."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("brr2pcm.py")


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="brr-cli-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def run_cli(self, *arguments, expected=0):
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, arguments)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def test_signed_pcm_and_budget(self):
        sample = self.root / "polarity.brr"
        sample.write_bytes(bytes([0xc1]) + bytes([0x78] * 8))
        out, manifest = self.root / "out.pcm", self.root / "out.json"
        self.run_cli(sample, "--out", out, "--manifest", manifest, "--budget", 15, expected=1)
        self.assertEqual(out.read_bytes(), bytes([112, 128] * 8))
        metadata = json.loads(manifest.read_text())
        self.assertEqual(metadata["total_pcm_bytes"], 16)
        self.assertFalse(metadata["fits_budget"])

    def test_external_loop_and_header_agree(self):
        data = bytes.fromhex("800123456789abcdef8789abcdef01234567")
        sample, prefixed = self.root / "raw.brr", self.root / "prefixed.brr"
        sample.write_bytes(data)
        prefixed.write_bytes(bytes([9, 0]) + data)
        out1, out2 = self.root / "raw.pcm", self.root / "prefixed.pcm"
        manifest = self.root / "loop.json"
        self.run_cli(sample, "--loop-offset", "0x9", "--loops", 2, "--out", out1,
                     "--manifest", manifest)
        self.run_cli(prefixed, "--loop-header", "--loops", 2, "--out", out2)
        self.assertEqual(out1.read_bytes(), out2.read_bytes())
        metadata = json.loads(manifest.read_text())["samples"][0]
        self.assertEqual(metadata["loop_pcm_offset"], 16)
        self.assertEqual(metadata["pcm_bytes"], 64)

    def test_batch_loop_map_and_end_stop(self):
        samples = self.root / "samples"
        samples.mkdir()
        (samples / "loop.brr").write_bytes(bytes([3]) + bytes(8))
        (samples / "stop.brr").write_bytes(bytes([1]) + bytes(17))
        mapping = self.root / "map.json"
        mapping.write_text('{"loop.brr": 0}')
        out, manifest = self.root / "pcm", self.root / "meta.json"
        self.run_cli(samples, "--loop-map", mapping, "--out", out, "--manifest", manifest)
        self.assertEqual(sorted(p.name for p in out.iterdir()), ["loop.pcm", "stop.pcm"])
        metadata = json.loads(manifest.read_text())
        self.assertEqual(metadata["total_pcm_bytes"], 32)
        self.assertEqual(metadata["samples"][0]["loop_pcm_offset"], 0)
        self.assertEqual(metadata["samples"][1]["trailing_bytes"], 9)

    def test_validation_precedes_writes_and_protects_inputs(self):
        good, bad = self.root / "a.brr", self.root / "b.brr"
        data = bytes([1]) + bytes(8)
        good.write_bytes(data)
        bad.write_bytes(bytes(8))
        out = self.root / "output"
        self.run_cli(good, bad, "--out", out, expected=1)
        self.assertFalse(out.exists())
        self.run_cli(good, "--out", good, expected=1)
        self.assertEqual(good.read_bytes(), data)
        self.run_cli(good, "--out", out, "--manifest", out, expected=1)
        self.assertFalse(out.exists())
        self.run_cli(good, "--loop-offset", 1, expected=1)
        self.run_cli(good, "--loops", 1, expected=1)


if __name__ == "__main__":
    unittest.main()
