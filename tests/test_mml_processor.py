#!/usr/bin/env python
"""
MMLプロセッサのテストコード
"""

import pytest
import tempfile
import os
from src.mml_processor import MMLProcessor


class TestMMLProcessor:
    """MMLプロセッサのテストクラス"""

    def setup_method(self):
        """テストメソッドの前処理"""
        self.processor = MMLProcessor()

    def test_simple_mml_parsing(self):
        """シンプルなMML解析のテスト"""
        mml = "CDEFGAB"
        stream = self.processor.parse_mml(mml)

        # ストリームが作成されることを確認
        assert stream is not None

        # 音符の数を確認（メタデータを除く）
        notes = [element for element in stream if hasattr(element, "pitch")]
        assert len(notes) == 7

    def test_mml_with_octave(self):
        """オクターブ指定付きMMLのテスト"""
        mml = "O4CDEFGAB"
        stream = self.processor.parse_mml(mml)

        notes = [element for element in stream if hasattr(element, "pitch")]
        assert len(notes) == 7

        # 最初の音符のオクターブを確認
        first_note = notes[0]
        assert first_note.pitch.octave == 4

    def test_mml_with_length(self):
        """音長指定付きMMLのテスト"""
        mml = "C4D8E2"
        stream = self.processor.parse_mml(mml)

        notes = [element for element in stream if hasattr(element, "pitch")]
        assert len(notes) == 3

        # 音長を確認
        assert notes[0].duration.quarterLength == 1.0  # 4分音符
        assert notes[1].duration.quarterLength == 0.5  # 8分音符
        assert notes[2].duration.quarterLength == 2.0  # 2分音符

    def test_mml_with_rest(self):
        """休符付きMMLのテスト"""
        mml = "CR4DR8E"
        stream = self.processor.parse_mml(mml)

        # 音符と休符の数を確認
        notes = [element for element in stream if hasattr(element, "pitch")]
        rests = [element for element in stream if hasattr(element, "isRest") and element.isRest]

        assert len(notes) == 3
        assert len(rests) == 2

    def test_mml_with_sharp_flat(self):
        """シャープ・フラット付きMMLのテスト"""
        mml = "C#D-E"
        stream = self.processor.parse_mml(mml)

        notes = [element for element in stream if hasattr(element, "pitch")]
        assert len(notes) == 3

        # シャープ・フラットを確認
        assert notes[0].pitch.name == "C#"
        assert notes[1].pitch.name == "D-"
        assert notes[2].pitch.name == "E"

    def test_mml_with_tempo(self):
        """テンポ指定付きMMLのテスト"""
        mml = "T120CDEFG"
        stream = self.processor.parse_mml(mml)

        # テンポ指定が含まれることを確認
        from music21 import tempo

        tempo_indications = [element for element in stream if isinstance(element, tempo.TempoIndication)]
        assert len(tempo_indications) > 0

    def test_mml_with_default_length(self):
        """デフォルト音長指定付きMMLのテスト"""
        mml = "L8CDEFG"
        stream = self.processor.parse_mml(mml)

        notes = [element for element in stream if hasattr(element, "pitch")]

        # 全ての音符が8分音符になることを確認
        for note in notes:
            assert note.duration.quarterLength == 0.5

    def test_mml_with_octave_change(self):
        """オクターブ変更記号付きMMLのテスト"""
        mml = "C>C<C"
        stream = self.processor.parse_mml(mml)

        notes = [element for element in stream if hasattr(element, "pitch")]
        assert len(notes) == 3

        # オクターブの変化を確認
        assert notes[0].pitch.octave == 4  # デフォルト
        assert notes[1].pitch.octave == 5  # >で上がる
        assert notes[2].pitch.octave == 4  # <で下がる

    def test_mml_with_dots(self):
        """付点音符付きMMLのテスト"""
        mml = "C4.D8."
        stream = self.processor.parse_mml(mml)

        notes = [element for element in stream if hasattr(element, "pitch")]
        assert len(notes) == 2

        # 付点音符の音長を確認
        assert notes[0].duration.quarterLength == 1.5  # 4分音符の付点
        assert notes[1].duration.quarterLength == 0.75  # 8分音符の付点

    def test_mml_to_midi_data(self):
        """MMLからMIDIデータ変換のテスト"""
        mml = "CDEFGAB"
        midi_data = self.processor.mml_to_midi_data(mml)

        # MIDIデータが生成されることを確認
        assert isinstance(midi_data, bytes)
        assert len(midi_data) > 0

        # MIDIファイルヘッダーを確認
        assert midi_data[:4] == b"MThd"

    def test_save_midi_file(self):
        """MIDIファイル保存のテスト"""
        mml = "CDEFGAB"
        midi_data = self.processor.mml_to_midi_data(mml)

        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # ファイルに保存
            self.processor.save_midi_file(midi_data, tmp_path)

            # ファイルが作成されることを確認
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 0

            # ファイル内容を確認
            with open(tmp_path, "rb") as f:
                saved_data = f.read()
            assert saved_data == midi_data

        finally:
            # テンポラリファイルを削除
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_validate_mml_syntax_valid(self):
        """正常なMML構文の検証テスト"""
        valid_mml = "O4L4CDEFGAB"
        is_valid, message = self.processor.validate_mml_syntax(valid_mml)

        assert is_valid is True
        assert "正常" in message

    def test_validate_mml_syntax_invalid(self):
        """不正なMML構文の検証テスト"""
        invalid_mml = "CDEFGABX"  # Xは不正な文字
        is_valid, message = self.processor.validate_mml_syntax(invalid_mml)

        assert is_valid is False
        assert "エラー" in message or "不明" in message

    def test_empty_mml(self):
        """空のMMLのテスト"""
        mml = ""
        stream = self.processor.parse_mml(mml)

        # 空のストリームでもメタデータは含まれる
        assert stream is not None

        # 音符は含まれない
        notes = [element for element in stream if hasattr(element, "pitch")]
        assert len(notes) == 0

    def test_whitespace_handling(self):
        """空白文字の処理テスト"""
        mml_with_spaces = "C D E F G"
        mml_without_spaces = "CDEFG"

        stream1 = self.processor.parse_mml(mml_with_spaces)
        stream2 = self.processor.parse_mml(mml_without_spaces)

        # 空白があってもなくても同じ結果になることを確認
        notes1 = [element for element in stream1 if hasattr(element, "pitch")]
        notes2 = [element for element in stream2 if hasattr(element, "pitch")]

        assert len(notes1) == len(notes2)

    def test_case_insensitive(self):
        """大文字小文字の処理テスト"""
        mml_upper = "CDEFG"
        mml_lower = "cdefg"

        stream1 = self.processor.parse_mml(mml_upper)
        stream2 = self.processor.parse_mml(mml_lower)

        # 大文字小文字に関係なく同じ結果になることを確認
        notes1 = [element for element in stream1 if hasattr(element, "pitch")]
        notes2 = [element for element in stream2 if hasattr(element, "pitch")]

        assert len(notes1) == len(notes2)


if __name__ == "__main__":
    pytest.main([__file__])
