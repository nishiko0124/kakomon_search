import sys
from pathlib import Path

# ルートディレクトリをパスに追加してローカルモジュールをインポート可能にする
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
