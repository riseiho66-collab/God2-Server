import base64
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.research import tool_inventory


class ToolInventoryTests(unittest.TestCase):
    def test_powershell_stops_on_cmdlet_failure(self):
        result = subprocess.CompletedProcess([], 1, b'', b'module load failed')
        with patch.object(tool_inventory.subprocess, 'run', return_value=result) as run:
            with self.assertRaisesRegex(RuntimeError, 'module load failed'):
                tool_inventory.powershell('Get-AuthenticodeSignature missing.exe')
        script = base64.b64decode(run.call_args.args[0][-1]).decode('utf-16le')
        self.assertTrue(script.startswith("$ErrorActionPreference='Stop'; "))

    def test_powershell_decodes_json(self):
        result = subprocess.CompletedProcess([], 0, b'{"signature_status":"Valid"}', b'')
        with patch.object(tool_inventory.subprocess, 'run', return_value=result):
            self.assertEqual(tool_inventory.powershell('unused'), {'signature_status': 'Valid'})

    def test_metadata_uses_security_module_from_actual_powershell_host(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'debugger.exe'
            path.touch()
            with patch.object(tool_inventory, 'powershell', return_value={}) as shell:
                with patch.object(tool_inventory.pefile, 'PE') as pe:
                    pe.return_value.__enter__.return_value.FILE_HEADER.Machine = 0x8664
                    info = tool_inventory.metadata(path)
            script = shell.call_args.args[0]
            self.assertIn("Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Security/", script)
            self.assertIn('Get-AuthenticodeSignature -LiteralPath $p', script)
            self.assertEqual(info['architecture'], 'x64')


if __name__ == '__main__':
    unittest.main()
