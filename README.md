# MML MCP Server

MML（Music Macro Language）を処理するModel Context Protocol (MCP)サーバーです。

## 概要

このプロジェクトは、MMLテキストの解析、MIDIファイルへの変換、MIDIデバイスでの演奏機能を提供するMCPサーバーです。LLMが音楽制作や演奏に関するタスクを実行できるようにします。

## 機能

### MCPサーバー基本機能
- JSON-RPC over stdioベースのMCPサーバー
- MCP標準プロトコルに準拠したAPIエンドポイント
- エラーハンドリングとロギング

### MML処理機能
- **MMLからMIDI変換**: MMLテキストをMIDIファイルに変換して保存
- **MIDI演奏**: MIDIファイルをMIDIデバイスで演奏
- **MML演奏**: MMLテキストを直接演奏（内部でMIDI変換）
- **MML構文検証**: MML構文の正確性をチェック
- **MIDIデバイス一覧**: 利用可能なMIDIデバイスの表示

### サンプルツール
- `get_system_info`: システム情報を取得
- `get_current_time`: 現在の日時を取得
- `echo`: 入力されたテキストをそのまま返す

## 必要な環境

- Python 3.10以上
- pip または uv
- MIDIデバイス（演奏機能を使用する場合）

## インストール

### 依存関係のインストール

#### uvを使用する場合（推奨）

```bash
# uvがインストールされていない場合は先にインストール
# pip install uv

# 依存関係のインストール
uv sync
```

#### pipを使用する場合

```bash
# リポジトリをクローン
git clone <repository-url>
cd mcp-mml-server

# 依存関係をインストール
pip install -e .
```

## 使用方法

### MCPサーバーの起動

#### uvを使用する場合（推奨）

```bash
uv run python -m src.main
```

オプションを指定する場合：

```bash
uv run python -m src.main --name "mml-server" --version "1.0.0" --description "MML Processing Server"
```

#### 通常のPythonを使用する場合

```bash
python -m src.main
```

オプションを指定する場合：

```bash
python -m src.main --name "mml-server" --version "1.0.0" --description "MML Processing Server"
```

### Cline/Cursorでの設定

Cline/CursorなどのAIツールでMCPサーバーを使用するには、`mcp_settings.json`ファイルに以下のような設定を追加します：

```json
"mml-mcp-server": {
  "command": "uv",
  "args": [
    "run",
    "--directory",
    "/path/to/mcp-mml-server",
    "python",
    "-m",
    "src.main"
  ],
  "env": {},
  "disabled": false,
  "alwaysAllow": []
}
```

`/path/to/mcp-mml-server`は、このリポジトリのインストールディレクトリに置き換えてください。

## MMLツール

### 1. MMLからMIDI変換 (`mml_to_midi`)

MMLテキストをMIDIファイルに変換します。

**パラメータ:**
- `mml_text` (string): 変換するMMLテキスト
- `output_path` (string): 出力MIDIファイルのパス

**例:**
```json
{
  "mml_text": "O4L4CDEFGAB",
  "output_path": "output.mid"
}
```

### 2. MIDI演奏 (`play_midi`)

MIDIファイルをMIDIデバイスで演奏します。

**パラメータ:**
- `midi_path` (string): 演奏するMIDIファイルのパス
- `device_name` (string, optional): 使用するMIDIデバイス名

**例:**
```json
{
  "midi_path": "music.mid",
  "device_name": "MIDI Device"
}
```

### 3. MML演奏 (`play_mml`)

MMLテキストを直接演奏します。

**パラメータ:**
- `mml_text` (string): 演奏するMMLテキスト
- `device_name` (string, optional): 使用するMIDIデバイス名

**例:**
```json
{
  "mml_text": "O4L4CDEFGAB>C",
  "device_name": "MIDI Device"
}
```

### 4. MML構文検証 (`validate_mml`)

MML構文の正確性をチェックします。

**パラメータ:**
- `mml_text` (string): 検証するMMLテキスト

**例:**
```json
{
  "mml_text": "O4L4CDEFGAB"
}
```

### 5. MIDIデバイス一覧 (`list_midi_devices`)

利用可能なMIDIデバイスの一覧を取得します。

**パラメータ:** なし

## MML記法

このサーバーでサポートされているMML記法：

### 基本音符
- `C`, `D`, `E`, `F`, `G`, `A`, `B`: ドレミファソラシ
- `C#`, `D#`, `F#`, `G#`, `A#`: シャープ
- `C-`, `D-`, `E-`, `G-`, `A-`, `B-`: フラット

### 音長指定
- `C4`: 4分音符のド
- `C8`: 8分音符のド
- `C2`: 2分音符のド
- `C1`: 全音符のド
- `C4.`: 付点4分音符のド

### 休符
- `R4`: 4分休符
- `R8`: 8分休符

### オクターブ
- `O4`: オクターブを4に設定
- `>`: オクターブを1つ上げる
- `<`: オクターブを1つ下げる

### その他
- `L4`: デフォルト音長を4分音符に設定
- `T120`: テンポを120BPMに設定

### MMLの例

```
# 基本的なスケール
O4L4CDEFGAB>C

# テンポとオクターブを指定した楽曲
T120O5L8CDEFGAB>C2

# 付点音符と休符を含む楽曲
O4L4C.D8EFG2R4AB>C

# シャープ・フラットを含む楽曲
O4L4CC#DD-EFF#GG#AA-B>C
```

## 開発

### テストの実行

```bash
# uvを使用する場合
uv run pytest

# pipを使用する場合
pytest
```

### 開発用依存関係のインストール

```bash
pip install -e ".[dev]"
```

### カスタムツールの追加

独自のツールを追加するには、以下の手順に従ってください：

1. ツール関数を作成
2. `register_tools`関数でツールを登録
3. メイン関数で登録関数を呼び出し

**例:**

```python
def my_custom_tool(params):
    # ツールの処理
    return {
        "content": [
            {
                "type": "text",
                "text": "結果",
            }
        ]
    }

def register_my_tools(server):
    server.register_tool(
        name="my_tool",
        description="My custom tool",
        input_schema={
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Parameter 1",
                },
            },
            "required": ["param1"],
        },
        handler=my_custom_tool,
    )
```

## トラブルシューティング

### MIDIデバイスが見つからない場合

1. システムにMIDIデバイスが接続されているか確認
2. `list_midi_devices`ツールで利用可能なデバイスを確認
3. 仮想MIDIポートの使用を検討

### MML構文エラーの場合

1. `validate_mml`ツールで構文をチェック
2. サポートされているMML記法を確認
3. 不正な文字や記号が含まれていないか確認

### 依存関係のエラーの場合

MIDIライブラリの依存関係でエラーが発生する場合：

**macOS:**
```bash
# Core MIDIが必要
# 通常は自動的にインストールされています
```

**Linux:**
```bash
# ALSA開発ライブラリが必要
sudo apt-get install libasound2-dev
# または
sudo yum install alsa-lib-devel
```

**Windows:**
```bash
# Windows MIDIが必要
# 通常は自動的に利用可能です
```

## ライセンス

MIT License

## 貢献

プルリクエストやイシューの報告を歓迎します。

## 関連リンク

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Music21 Documentation](https://web.mit.edu/music21/)
- [MIDO Documentation](https://mido.readthedocs.io/)
