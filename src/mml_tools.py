#!/usr/bin/env python
"""
MML ツール

MML処理に関するMCPツールを提供します。
"""

import os
from typing import Dict, Any
from .mml_processor import MMLProcessor
from .midi_player import MIDIPlayer


def register_mml_tools(server) -> None:
    """MMLツールをMCPサーバーに登録します。

    Args:
        server: MCPサーバーインスタンス
    """

    # MML to MIDI変換ツール
    server.register_tool(
        name="mml_to_midi",
        description="MMLテキストをMIDIファイルに変換して保存します",
        input_schema={
            "type": "object",
            "properties": {
                "mml_text": {"type": "string", "description": "変換するMMLテキスト（例: 'CDEFGAB'）"},
                "output_path": {"type": "string", "description": "出力MIDIファイルのパス（例: 'output.mid'）"},
            },
            "required": ["mml_text", "output_path"],
        },
        handler=mml_to_midi,
    )

    # MIDI演奏ツール
    server.register_tool(
        name="play_midi",
        description="MIDIファイルをMIDIデバイスで演奏します",
        input_schema={
            "type": "object",
            "properties": {
                "midi_path": {"type": "string", "description": "演奏するMIDIファイルのパス"},
                "device_name": {"type": "string", "description": "使用するMIDIデバイス名（省略時はデフォルトデバイス）"},
            },
            "required": ["midi_path"],
        },
        handler=play_midi,
    )

    # MML演奏ツール
    server.register_tool(
        name="play_mml",
        description="MMLテキストを直接演奏します（内部でMIDI変換）",
        input_schema={
            "type": "object",
            "properties": {
                "mml_text": {"type": "string", "description": "演奏するMMLテキスト（例: 'CDEFGAB'）"},
                "device_name": {"type": "string", "description": "使用するMIDIデバイス名（省略時はデフォルトデバイス）"},
            },
            "required": ["mml_text"],
        },
        handler=play_mml,
    )

    # MMLバリデーションツール
    server.register_tool(
        name="validate_mml",
        description="MML構文を検証します",
        input_schema={
            "type": "object",
            "properties": {"mml_text": {"type": "string", "description": "検証するMMLテキスト"}},
            "required": ["mml_text"],
        },
        handler=validate_mml,
    )

    # MIDIデバイス一覧ツール
    server.register_tool(
        name="list_midi_devices",
        description="利用可能なMIDIデバイスの一覧を取得します",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=list_midi_devices,
    )

    # マルチトラックMML to MIDI変換ツール
    server.register_tool(
        name="mml_multitrack_to_midi",
        description="複数のMMLテキストをマルチトラックMIDIファイルに変換して保存します",
        input_schema={
            "type": "object",
            "properties": {
                "track_mml_list": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "各トラックのMMLテキストのリスト（例: ['CDEFGAB', 'EGBEGB']）",
                },
                "output_path": {"type": "string", "description": "出力MIDIファイルのパス（例: 'multitrack.mid'）"},
            },
            "required": ["track_mml_list", "output_path"],
        },
        handler=mml_multitrack_to_midi,
    )

    # マルチトラックMML演奏ツール
    server.register_tool(
        name="play_mml_multitrack",
        description="複数のMMLテキストをマルチトラックで直接演奏します",
        input_schema={
            "type": "object",
            "properties": {
                "track_mml_list": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "各トラックのMMLテキストのリスト（例: ['CDEFGAB', 'EGBEGB']）",
                },
                "device_name": {"type": "string", "description": "使用するMIDIデバイス名（省略時はデフォルトデバイス）"},
            },
            "required": ["track_mml_list"],
        },
        handler=play_mml_multitrack,
    )


def mml_to_midi(params: Dict[str, Any]) -> Dict[str, Any]:
    """MMLテキストをMIDIファイルに変換します。

    Args:
        params (Dict[str, Any]): パラメータ辞書
            - mml_text (str): MMLテキスト
            - output_path (str): 出力ファイルパス

    Returns:
        Dict[str, Any]: 実行結果
    """
    try:
        mml_text = params.get("mml_text")
        output_path = params.get("output_path")

        if not mml_text:
            raise ValueError("mml_textパラメータが必要です")
        if not output_path:
            raise ValueError("output_pathパラメータが必要です")

        # MMLプロセッサを作成
        processor = MMLProcessor()

        # MMLをMIDIデータに変換
        midi_data = processor.mml_to_midi_data(mml_text)

        # ファイルに保存
        processor.save_midi_file(midi_data, output_path)

        # ファイルサイズを取得
        file_size = os.path.getsize(output_path)

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"MMLをMIDIファイルに変換しました。\n"
                    f"入力MML: {mml_text[:100]}{'...' if len(mml_text) > 100 else ''}\n"
                    f"出力ファイル: {output_path}\n"
                    f"ファイルサイズ: {file_size} bytes",
                }
            ]
        }

    except Exception as e:
        return {"content": [{"type": "text", "text": f"MML to MIDI変換エラー: {str(e)}"}], "isError": True}


def play_midi(params: Dict[str, Any]) -> Dict[str, Any]:
    """MIDIファイルを演奏します。

    Args:
        params (Dict[str, Any]): パラメータ辞書
            - midi_path (str): MIDIファイルパス
            - device_name (str, optional): MIDIデバイス名

    Returns:
        Dict[str, Any]: 実行結果
    """
    try:
        midi_path = params.get("midi_path")
        device_name = params.get("device_name")

        if not midi_path:
            raise ValueError("midi_pathパラメータが必要です")

        # MIDIプレイヤーを作成
        player = MIDIPlayer(device_name=device_name)

        # MIDIファイルを演奏
        player.play_midi_file(midi_path)

        # デバイス情報を取得
        device_info = player.get_device_info()

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"MIDIファイルの演奏を開始しました。\n"
                    f"ファイル: {midi_path}\n"
                    f"使用デバイス: {device_info['current_device']}\n"
                    f"演奏状態: {'演奏中' if device_info['is_playing'] else '停止中'}",
                }
            ]
        }

    except Exception as e:
        return {"content": [{"type": "text", "text": f"MIDI演奏エラー: {str(e)}"}], "isError": True}


def play_mml(params: Dict[str, Any]) -> Dict[str, Any]:
    """MMLテキストを直接演奏します。

    Args:
        params (Dict[str, Any]): パラメータ辞書
            - mml_text (str): MMLテキスト
            - device_name (str, optional): MIDIデバイス名

    Returns:
        Dict[str, Any]: 実行結果
    """
    try:
        mml_text = params.get("mml_text")
        device_name = params.get("device_name")

        if not mml_text:
            raise ValueError("mml_textパラメータが必要です")

        # MMLプロセッサを作成
        processor = MMLProcessor()

        # MMLをMIDIデータに変換
        midi_data = processor.mml_to_midi_data(mml_text)

        # MIDIプレイヤーを作成
        player = MIDIPlayer(device_name=device_name)

        # MIDIデータを演奏
        player.play_midi_data(midi_data)

        # デバイス情報を取得
        device_info = player.get_device_info()

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"MMLの演奏を開始しました。\n"
                    f"MML: {mml_text[:100]}{'...' if len(mml_text) > 100 else ''}\n"
                    f"使用デバイス: {device_info['current_device']}\n"
                    f"演奏状態: {'演奏中' if device_info['is_playing'] else '停止中'}",
                }
            ]
        }

    except Exception as e:
        return {"content": [{"type": "text", "text": f"MML演奏エラー: {str(e)}"}], "isError": True}


def validate_mml(params: Dict[str, Any]) -> Dict[str, Any]:
    """MML構文を検証します。

    Args:
        params (Dict[str, Any]): パラメータ辞書
            - mml_text (str): MMLテキスト

    Returns:
        Dict[str, Any]: 実行結果
    """
    try:
        mml_text = params.get("mml_text")

        if not mml_text:
            raise ValueError("mml_textパラメータが必要です")

        # MMLプロセッサを作成
        processor = MMLProcessor()

        # MML構文を検証
        is_valid, message = processor.validate_mml_syntax(mml_text)

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"MML構文検証結果:\n"
                    f"MML: {mml_text[:100]}{'...' if len(mml_text) > 100 else ''}\n"
                    f"結果: {'✓ 正常' if is_valid else '✗ エラー'}\n"
                    f"詳細: {message}",
                }
            ],
            "isError": not is_valid,
        }

    except Exception as e:
        return {"content": [{"type": "text", "text": f"MML検証エラー: {str(e)}"}], "isError": True}


def list_midi_devices(params: Dict[str, Any]) -> Dict[str, Any]:
    """利用可能なMIDIデバイスの一覧を取得します。

    Args:
        params (Dict[str, Any]): パラメータ辞書（未使用）

    Returns:
        Dict[str, Any]: 実行結果
    """
    try:
        # MIDIプレイヤーを作成
        player = MIDIPlayer()

        # 利用可能なデバイス一覧を取得
        devices = player.get_available_devices()

        if not devices:
            device_list = "利用可能なMIDIデバイスがありません。\n仮想MIDIポートが作成されます。"
        else:
            device_list = "利用可能なMIDIデバイス:\n" + "\n".join(f"- {device}" for device in devices)

        return {"content": [{"type": "text", "text": f"MIDIデバイス一覧:\n\n{device_list}"}]}

    except Exception as e:
        return {"content": [{"type": "text", "text": f"MIDIデバイス一覧取得エラー: {str(e)}"}], "isError": True}


def mml_multitrack_to_midi(params: Dict[str, Any]) -> Dict[str, Any]:
    """複数のMMLテキストをマルチトラックMIDIファイルに変換します。

    Args:
        params (Dict[str, Any]): パラメータ辞書
            - track_mml_list (list): MMLテキストのリスト
            - output_path (str): 出力ファイルパス

    Returns:
        Dict[str, Any]: 実行結果
    """
    try:
        track_mml_list = params.get("track_mml_list")
        output_path = params.get("output_path")

        if not track_mml_list:
            raise ValueError("track_mml_listパラメータが必要です")
        if not output_path:
            raise ValueError("output_pathパラメータが必要です")
        if not isinstance(track_mml_list, list):
            raise ValueError("track_mml_listはリストである必要があります")

        # MMLプロセッサを作成
        processor = MMLProcessor()

        # マルチトラックMMLをMIDIデータに変換
        midi_data = processor.mml_multitrack_to_midi_data(track_mml_list)

        # ファイルに保存
        processor.save_midi_file(midi_data, output_path)

        # ファイルサイズを取得
        file_size = os.path.getsize(output_path)

        # トラック情報を作成
        track_info = "\n".join(
            [f"トラック{i + 1}: {mml[:50]}{'...' if len(mml) > 50 else ''}" for i, mml in enumerate(track_mml_list)]
        )

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"マルチトラックMMLをMIDIファイルに変換しました。\n"
                    f"トラック数: {len(track_mml_list)}\n"
                    f"{track_info}\n"
                    f"出力ファイル: {output_path}\n"
                    f"ファイルサイズ: {file_size} bytes",
                }
            ]
        }

    except Exception as e:
        return {"content": [{"type": "text", "text": f"マルチトラックMML to MIDI変換エラー: {str(e)}"}], "isError": True}


def play_mml_multitrack(params: Dict[str, Any]) -> Dict[str, Any]:
    """複数のMMLテキストをマルチトラックで直接演奏します。

    Args:
        params (Dict[str, Any]): パラメータ辞書
            - track_mml_list (list): MMLテキストのリスト
            - device_name (str, optional): MIDIデバイス名

    Returns:
        Dict[str, Any]: 実行結果
    """
    try:
        track_mml_list = params.get("track_mml_list")
        device_name = params.get("device_name")

        if not track_mml_list:
            raise ValueError("track_mml_listパラメータが必要です")
        if not isinstance(track_mml_list, list):
            raise ValueError("track_mml_listはリストである必要があります")

        # MMLプロセッサを作成
        processor = MMLProcessor()

        # マルチトラックMMLをMIDIデータに変換
        midi_data = processor.mml_multitrack_to_midi_data(track_mml_list)

        # MIDIプレイヤーを作成
        player = MIDIPlayer(device_name=device_name)

        # MIDIデータを演奏
        player.play_midi_data(midi_data)

        # デバイス情報を取得
        device_info = player.get_device_info()

        # トラック情報を作成
        track_info = "\n".join(
            [f"トラック{i + 1}: {mml[:50]}{'...' if len(mml) > 50 else ''}" for i, mml in enumerate(track_mml_list)]
        )

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"マルチトラックMMLの演奏を開始しました。\n"
                    f"トラック数: {len(track_mml_list)}\n"
                    f"{track_info}\n"
                    f"使用デバイス: {device_info['current_device']}\n"
                    f"演奏状態: {'演奏中' if device_info['is_playing'] else '停止中'}",
                }
            ]
        }

    except Exception as e:
        return {"content": [{"type": "text", "text": f"マルチトラックMML演奏エラー: {str(e)}"}], "isError": True}
