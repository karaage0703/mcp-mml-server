#!/usr/bin/env python
"""
MMLツールのテストコード
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from src.mml_tools import mml_to_midi, play_midi, play_mml, validate_mml, list_midi_devices


class TestMMLTools:
    """MMLツールのテストクラス"""

    def test_mml_to_midi_success(self):
        """MML to MIDI変換の成功テスト"""
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            params = {"mml_text": "CDEFGAB", "output_path": tmp_path}

            result = mml_to_midi(params)

            # 成功結果を確認
            assert "isError" not in result
            assert len(result["content"]) == 1
            assert "変換しました" in result["content"][0]["text"]

            # ファイルが作成されることを確認
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 0

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_mml_to_midi_missing_params(self):
        """MML to MIDI変換のパラメータ不足テスト"""
        # mml_textが不足
        params = {"output_path": "test.mid"}
        result = mml_to_midi(params)

        assert result["isError"] is True
        assert "mml_textパラメータが必要" in result["content"][0]["text"]

        # output_pathが不足
        params = {"mml_text": "CDEFG"}
        result = mml_to_midi(params)

        assert result["isError"] is True
        assert "output_pathパラメータが必要" in result["content"][0]["text"]

    def test_mml_to_midi_invalid_mml(self):
        """MML to MIDI変換の不正MMLテスト"""
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            params = {
                "mml_text": "CDEFGABX",  # Xは不正な文字
                "output_path": tmp_path,
            }

            result = mml_to_midi(params)

            # エラー結果を確認
            assert result["isError"] is True
            assert "エラー" in result["content"][0]["text"]

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch("src.mml_tools.MIDIPlayer")
    def test_play_midi_success(self, mock_player_class):
        """MIDI演奏の成功テスト"""
        # モックの設定
        mock_player = Mock()
        mock_player.get_device_info.return_value = {"current_device": "テストデバイス", "is_playing": True}
        mock_player_class.return_value = mock_player

        # テンポラリMIDIファイルを作成
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            # 簡単なMIDIデータを書き込み
            tmp_file.write(b"MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60")

        try:
            params = {"midi_path": tmp_path}
            result = play_midi(params)

            # 成功結果を確認
            assert "isError" not in result
            assert "演奏を開始しました" in result["content"][0]["text"]

            # MIDIプレイヤーが呼び出されることを確認
            mock_player_class.assert_called_once_with(device_name=None)
            mock_player.play_midi_file.assert_called_once_with(tmp_path)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_play_midi_file_not_found(self):
        """MIDI演奏のファイル未発見テスト"""
        params = {"midi_path": "nonexistent.mid"}
        result = play_midi(params)

        assert result["isError"] is True
        assert "見つかりません" in result["content"][0]["text"]

    def test_play_midi_missing_params(self):
        """MIDI演奏のパラメータ不足テスト"""
        params = {}
        result = play_midi(params)

        assert result["isError"] is True
        assert "midi_pathパラメータが必要" in result["content"][0]["text"]

    @patch("src.mml_tools.MIDIPlayer")
    @patch("src.mml_tools.MMLProcessor")
    def test_play_mml_success(self, mock_processor_class, mock_player_class):
        """MML演奏の成功テスト"""
        # モックの設定
        mock_processor = Mock()
        mock_processor.mml_to_midi_data.return_value = b"mock_midi_data"
        mock_processor_class.return_value = mock_processor

        mock_player = Mock()
        mock_player.get_device_info.return_value = {"current_device": "テストデバイス", "is_playing": True}
        mock_player_class.return_value = mock_player

        params = {"mml_text": "CDEFGAB"}
        result = play_mml(params)

        # 成功結果を確認
        assert "isError" not in result
        assert "演奏を開始しました" in result["content"][0]["text"]

        # 各コンポーネントが呼び出されることを確認
        mock_processor.mml_to_midi_data.assert_called_once_with("CDEFGAB")
        mock_player.play_midi_data.assert_called_once_with(b"mock_midi_data")

    def test_play_mml_missing_params(self):
        """MML演奏のパラメータ不足テスト"""
        params = {}
        result = play_mml(params)

        assert result["isError"] is True
        assert "mml_textパラメータが必要" in result["content"][0]["text"]

    @patch("src.mml_tools.MMLProcessor")
    def test_validate_mml_valid(self, mock_processor_class):
        """MML検証の正常テスト"""
        # モックの設定
        mock_processor = Mock()
        mock_processor.validate_mml_syntax.return_value = (True, "MML構文は正常です")
        mock_processor_class.return_value = mock_processor

        params = {"mml_text": "CDEFGAB"}
        result = validate_mml(params)

        # 成功結果を確認
        assert result.get("isError") is not True
        assert "✓ 正常" in result["content"][0]["text"]

        mock_processor.validate_mml_syntax.assert_called_once_with("CDEFGAB")

    @patch("src.mml_tools.MMLProcessor")
    def test_validate_mml_invalid(self, mock_processor_class):
        """MML検証の異常テスト"""
        # モックの設定
        mock_processor = Mock()
        mock_processor.validate_mml_syntax.return_value = (False, "不明なMMLコマンド")
        mock_processor_class.return_value = mock_processor

        params = {"mml_text": "CDEFGABX"}
        result = validate_mml(params)

        # エラー結果を確認
        assert result["isError"] is True
        assert "✗ エラー" in result["content"][0]["text"]

    def test_validate_mml_missing_params(self):
        """MML検証のパラメータ不足テスト"""
        params = {}
        result = validate_mml(params)

        assert result["isError"] is True
        assert "mml_textパラメータが必要" in result["content"][0]["text"]

    @patch("src.mml_tools.MIDIPlayer")
    def test_list_midi_devices_with_devices(self, mock_player_class):
        """MIDIデバイス一覧の取得テスト（デバイスあり）"""
        # モックの設定
        mock_player = Mock()
        mock_player.get_available_devices.return_value = ["デバイス1", "デバイス2", "デバイス3"]
        mock_player_class.return_value = mock_player

        params = {}
        result = list_midi_devices(params)

        # 成功結果を確認
        assert "isError" not in result
        assert "利用可能なMIDIデバイス:" in result["content"][0]["text"]
        assert "デバイス1" in result["content"][0]["text"]
        assert "デバイス2" in result["content"][0]["text"]
        assert "デバイス3" in result["content"][0]["text"]

    @patch("src.mml_tools.MIDIPlayer")
    def test_list_midi_devices_no_devices(self, mock_player_class):
        """MIDIデバイス一覧の取得テスト（デバイスなし）"""
        # モックの設定
        mock_player = Mock()
        mock_player.get_available_devices.return_value = []
        mock_player_class.return_value = mock_player

        params = {}
        result = list_midi_devices(params)

        # 成功結果を確認
        assert "isError" not in result
        assert "利用可能なMIDIデバイスがありません" in result["content"][0]["text"]
        assert "仮想MIDIポート" in result["content"][0]["text"]

    @patch("src.mml_tools.MIDIPlayer")
    def test_list_midi_devices_error(self, mock_player_class):
        """MIDIデバイス一覧の取得エラーテスト"""
        # モックの設定
        mock_player_class.side_effect = Exception("テストエラー")

        params = {}
        result = list_midi_devices(params)

        # エラー結果を確認
        assert result["isError"] is True
        assert "エラー" in result["content"][0]["text"]

    def test_long_mml_text_truncation(self):
        """長いMMLテキストの切り詰めテスト"""
        # 100文字を超えるMMLテキスト
        long_mml = "C" * 150

        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            params = {"mml_text": long_mml, "output_path": tmp_path}

            result = mml_to_midi(params)

            # 結果にテキストが切り詰められていることを確認
            result_text = result["content"][0]["text"]
            assert "..." in result_text
            assert len([line for line in result_text.split("\n") if "MML:" in line][0]) < len(f"入力MML: {long_mml}")

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == "__main__":
    pytest.main([__file__])
