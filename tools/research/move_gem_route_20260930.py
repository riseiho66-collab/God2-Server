from pathlib import Path

root = Path(__file__).resolve().parents[2]
path = root / 'src/core/Application.cpp'
source = path.read_text('utf-8')
start = source.index('                            // CUSTOM-0057: native gem25/26')
end = source.index('                            // CUSTOM-0046: qualify the entire28/weapon24 frame', start)
block = source[start:end]
source = source[:start] + source[end:]
anchor = '                            // CUSTOM-0050: ordinary owned self-player supply.'
position = source.index(anchor)
source = source[:position] + block + source[position:]
path.write_text(source, encoding='utf-8', newline='\n')
