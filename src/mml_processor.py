#!/usr/bin/env python
"""
MML (Music Macro Language) プロセッサ

MMLテキストの解析、MIDI変換、バリデーション機能を提供します。
"""

import re
import io
from typing import Tuple, Dict, Any, Optional
from music21 import stream, note, duration, tempo, meter, key
import mido


class MMLProcessor:
    """MML処理クラス

    MMLテキストの解析、MIDI変換、バリデーション機能を提供します。
    """

    def __init__(self):
        """MMLプロセッサを初期化します。"""
        self.default_octave = 4
        self.default_length = 4  # 4分音符
        self.default_tempo = 120

    def parse_mml(self, mml_text: str) -> stream.Stream:
        """MMLテキストを解析してmusic21のStreamオブジェクトに変換します。

        Args:
            mml_text (str): MMLテキスト

        Returns:
            stream.Stream: 解析されたmusic21ストリーム

        Raises:
            ValueError: MML構文エラーの場合
        """
        try:
            # MMLテキストの前処理（空白、改行を除去）
            mml_text = re.sub(r"\s+", "", mml_text.upper())

            # 新しいストリームを作成
            score = stream.Stream()

            # デフォルト設定
            current_octave = self.default_octave
            current_length = self.default_length
            current_tempo = self.default_tempo

            # テンポ設定
            score.append(tempo.TempoIndication(number=current_tempo))

            # 拍子設定（4/4拍子）
            score.append(meter.TimeSignature("4/4"))

            # 調設定（C major）
            score.append(key.KeySignature(0))

            # MMLコマンドの解析
            i = 0
            while i < len(mml_text):
                char = mml_text[i]

                if char in "CDEFGAB":
                    # 音符の処理
                    note_name = char
                    i += 1

                    # シャープ・フラットの処理
                    if i < len(mml_text) and mml_text[i] in "#+":
                        note_name += "#"
                        i += 1
                    elif i < len(mml_text) and mml_text[i] == "-":
                        note_name += "b"
                        i += 1

                    # 音長の処理
                    note_length = current_length
                    if i < len(mml_text) and mml_text[i].isdigit():
                        length_str = ""
                        while i < len(mml_text) and mml_text[i].isdigit():
                            length_str += mml_text[i]
                            i += 1
                        note_length = int(length_str)

                    # ドットの処理（付点音符）
                    dots = 0
                    while i < len(mml_text) and mml_text[i] == ".":
                        dots += 1
                        i += 1

                    # 音符を作成
                    pitch_name = f"{note_name}{current_octave}"
                    note_obj = note.Note(pitch_name)

                    # 音長を設定
                    quarter_length = 4.0 / note_length
                    if dots > 0:
                        # 付点音符の処理
                        for _ in range(dots):
                            quarter_length *= 1.5

                    note_obj.duration = duration.Duration(quarterLength=quarter_length)
                    score.append(note_obj)

                elif char == "R":
                    # 休符の処理
                    i += 1

                    # 音長の処理
                    rest_length = current_length
                    if i < len(mml_text) and mml_text[i].isdigit():
                        length_str = ""
                        while i < len(mml_text) and mml_text[i].isdigit():
                            length_str += mml_text[i]
                            i += 1
                        rest_length = int(length_str)

                    # ドットの処理
                    dots = 0
                    while i < len(mml_text) and mml_text[i] == ".":
                        dots += 1
                        i += 1

                    # 休符を作成
                    rest_obj = note.Rest()
                    quarter_length = 4.0 / rest_length
                    if dots > 0:
                        for _ in range(dots):
                            quarter_length *= 1.5

                    rest_obj.duration = duration.Duration(quarterLength=quarter_length)
                    score.append(rest_obj)

                elif char == "O":
                    # オクターブ設定
                    i += 1
                    if i < len(mml_text) and mml_text[i].isdigit():
                        current_octave = int(mml_text[i])
                        i += 1
                    else:
                        raise ValueError(f"オクターブ指定が不正です: 位置 {i}")

                elif char == "L":
                    # デフォルト音長設定
                    i += 1
                    if i < len(mml_text) and mml_text[i].isdigit():
                        length_str = ""
                        while i < len(mml_text) and mml_text[i].isdigit():
                            length_str += mml_text[i]
                            i += 1
                        current_length = int(length_str)
                    else:
                        raise ValueError(f"音長指定が不正です: 位置 {i}")

                elif char == "T":
                    # テンポ設定
                    i += 1
                    if i < len(mml_text) and mml_text[i].isdigit():
                        tempo_str = ""
                        while i < len(mml_text) and mml_text[i].isdigit():
                            tempo_str += mml_text[i]
                            i += 1
                        current_tempo = int(tempo_str)
                        score.append(tempo.TempoIndication(number=current_tempo))
                    else:
                        raise ValueError(f"テンポ指定が不正です: 位置 {i}")

                elif char == ">":
                    # オクターブ上げ
                    current_octave = min(current_octave + 1, 8)
                    i += 1

                elif char == "<":
                    # オクターブ下げ
                    current_octave = max(current_octave - 1, 0)
                    i += 1

                else:
                    # 不明な文字
                    raise ValueError(f"不明なMMLコマンド: '{char}' 位置 {i}")

            return score

        except Exception as e:
            raise ValueError(f"MML解析エラー: {str(e)}")

    def mml_to_midi_data(self, mml_text: str) -> bytes:
        """MMLテキストをMIDIデータに変換します。

        Args:
            mml_text (str): MMLテキスト

        Returns:
            bytes: MIDIデータ

        Raises:
            ValueError: MML構文エラーの場合
        """
        try:
            # MMLを解析
            score = self.parse_mml(mml_text)

            # MIDIファイルに変換
            midi_file = mido.MidiFile()
            track = mido.MidiTrack()
            midi_file.tracks.append(track)

            # デフォルト設定
            ticks_per_beat = midi_file.ticks_per_beat
            current_time = 0

            for element in score:
                if isinstance(element, note.Note):
                    # 音符の処理
                    midi_note = element.pitch.midi
                    velocity = 64  # デフォルトベロシティ

                    # 音符の長さをティックに変換
                    duration_ticks = int(element.duration.quarterLength * ticks_per_beat)

                    # Note On
                    track.append(mido.Message("note_on", channel=0, note=midi_note, velocity=velocity, time=current_time))

                    # Note Off
                    track.append(mido.Message("note_off", channel=0, note=midi_note, velocity=velocity, time=duration_ticks))

                    current_time = 0  # 次のイベントまでの時間をリセット

                elif isinstance(element, note.Rest):
                    # 休符の処理
                    duration_ticks = int(element.duration.quarterLength * ticks_per_beat)
                    current_time += duration_ticks

                elif isinstance(element, tempo.TempoIndication):
                    # テンポ変更
                    # music21のTempoIndicationオブジェクトからBPMを取得
                    bpm = element.numberSounding if hasattr(element, "numberSounding") else getattr(element, "number", 120)
                    microseconds_per_beat = int(60000000 / bpm)
                    track.append(mido.MetaMessage("set_tempo", tempo=microseconds_per_beat, time=current_time))
                    current_time = 0

            # MIDIデータをバイト列として取得
            midi_bytes = io.BytesIO()
            midi_file.save(file=midi_bytes)
            return midi_bytes.getvalue()

        except Exception as e:
            raise ValueError(f"MIDI変換エラー: {str(e)}")

    def mml_multitrack_to_midi_data(self, track_mml_list: list) -> bytes:
        """複数のMMLテキストをマルチトラックMIDIデータに変換します。

        Args:
            track_mml_list (list): MMLテキストのリスト（各要素が1トラック）

        Returns:
            bytes: マルチトラックMIDIデータ

        Raises:
            ValueError: MML構文エラーの場合
        """
        try:
            # MIDIファイルを作成
            midi_file = mido.MidiFile()
            ticks_per_beat = midi_file.ticks_per_beat

            for track_index, mml_text in enumerate(track_mml_list):
                # 各MMLを解析
                score = self.parse_mml(mml_text)

                # 新しいトラックを作成
                track = mido.MidiTrack()
                midi_file.tracks.append(track)

                # トラック名を設定
                track.append(mido.MetaMessage("track_name", name=f"Track {track_index + 1}", time=0))

                # MIDIチャンネルを設定（最大16チャンネル）
                channel = track_index % 16

                current_time = 0

                for element in score:
                    if isinstance(element, note.Note):
                        # 音符の処理
                        midi_note = element.pitch.midi
                        velocity = 64  # デフォルトベロシティ

                        # 音符の長さをティックに変換
                        duration_ticks = int(element.duration.quarterLength * ticks_per_beat)

                        # Note On
                        track.append(
                            mido.Message("note_on", channel=channel, note=midi_note, velocity=velocity, time=current_time)
                        )

                        # Note Off
                        track.append(
                            mido.Message("note_off", channel=channel, note=midi_note, velocity=velocity, time=duration_ticks)
                        )

                        current_time = 0

                    elif isinstance(element, note.Rest):
                        # 休符の処理
                        duration_ticks = int(element.duration.quarterLength * ticks_per_beat)
                        current_time += duration_ticks

                    elif isinstance(element, tempo.TempoIndication):
                        # テンポ変更（最初のトラックのみ）
                        if track_index == 0:
                            bpm = (
                                element.numberSounding
                                if hasattr(element, "numberSounding")
                                else getattr(element, "number", 120)
                            )
                            microseconds_per_beat = int(60000000 / bpm)
                            track.append(mido.MetaMessage("set_tempo", tempo=microseconds_per_beat, time=current_time))
                            current_time = 0

            # MIDIデータをバイト列として取得
            midi_bytes = io.BytesIO()
            midi_file.save(file=midi_bytes)
            return midi_bytes.getvalue()

        except Exception as e:
            raise ValueError(f"マルチトラックMIDI変換エラー: {str(e)}")

    def save_midi_file(self, midi_data: bytes, filepath: str) -> None:
        """MIDIデータをファイルに保存します。

        Args:
            midi_data (bytes): MIDIデータ
            filepath (str): 保存先ファイルパス

        Raises:
            IOError: ファイル保存エラーの場合
        """
        try:
            with open(filepath, "wb") as f:
                f.write(midi_data)
        except Exception as e:
            raise IOError(f"MIDIファイル保存エラー: {str(e)}")

    def validate_mml_syntax(self, mml_text: str) -> Tuple[bool, str]:
        """MML構文を検証します。

        Args:
            mml_text (str): MMLテキスト

        Returns:
            Tuple[bool, str]: (検証結果, エラーメッセージ)
        """
        try:
            # MMLを解析してみる
            self.parse_mml(mml_text)
            return True, "MML構文は正常です"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"予期しないエラー: {str(e)}"
