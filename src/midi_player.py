#!/usr/bin/env python
"""
MIDI プレイヤー

MIDIファイルやMIDIデータの演奏機能を提供します。
"""

import time
import threading
from typing import List, Optional, Dict, Any
import mido
import rtmidi


class MIDIPlayer:
    """MIDIプレイヤークラス

    MIDIファイルやMIDIデータの演奏機能を提供します。
    """

    def __init__(self, device_name: Optional[str] = None):
        """MIDIプレイヤーを初期化します。

        Args:
            device_name (Optional[str]): 使用するMIDIデバイス名。Noneの場合はデフォルトデバイスを使用
        """
        self.device_name = device_name
        self.midi_out = None
        self.is_playing = False
        self.play_thread = None

        # MIDIアウトポートを初期化
        self._initialize_midi_output()

    def _initialize_midi_output(self) -> None:
        """MIDIアウトポートを初期化します。"""
        try:
            self.midi_out = rtmidi.MidiOut()

            # 利用可能なポートを取得
            available_ports = self.midi_out.get_ports()

            if not available_ports:
                # 仮想ポートを作成
                self.midi_out.open_virtual_port("MML MCP Server")
                return

            # 指定されたデバイスを探す
            if self.device_name:
                for i, port_name in enumerate(available_ports):
                    if self.device_name.lower() in port_name.lower():
                        self.midi_out.open_port(i)
                        return

                # 指定されたデバイスが見つからない場合はエラー
                raise ValueError(f"指定されたMIDIデバイスが見つかりません: {self.device_name}")
            else:
                # デフォルトポート（最初のポート）を使用
                self.midi_out.open_port(0)

        except Exception as e:
            raise RuntimeError(f"MIDI出力の初期化に失敗しました: {str(e)}")

    def get_available_devices(self) -> List[str]:
        """利用可能なMIDIデバイスの一覧を取得します。

        Returns:
            List[str]: 利用可能なMIDIデバイス名のリスト
        """
        try:
            midi_out = rtmidi.MidiOut()
            return midi_out.get_ports()
        except Exception as e:
            raise RuntimeError(f"MIDIデバイス一覧の取得に失敗しました: {str(e)}")

    def play_midi_file(self, filepath: str) -> None:
        """MIDIファイルを演奏します。

        Args:
            filepath (str): MIDIファイルのパス

        Raises:
            FileNotFoundError: ファイルが見つからない場合
            RuntimeError: 演奏エラーの場合
        """
        try:
            # MIDIファイルを読み込み
            midi_file = mido.MidiFile(filepath)
            self.play_midi_data_from_file(midi_file)

        except FileNotFoundError:
            raise FileNotFoundError(f"MIDIファイルが見つかりません: {filepath}")
        except Exception as e:
            raise RuntimeError(f"MIDIファイル演奏エラー: {str(e)}")

    def play_midi_data(self, midi_data: bytes) -> None:
        """MIDIデータを演奏します。

        Args:
            midi_data (bytes): MIDIデータ

        Raises:
            RuntimeError: 演奏エラーの場合
        """
        try:
            # バイトデータからMIDIファイルオブジェクトを作成
            import io

            midi_file = mido.MidiFile(file=io.BytesIO(midi_data))
            self.play_midi_data_from_file(midi_file)

        except Exception as e:
            raise RuntimeError(f"MIDIデータ演奏エラー: {str(e)}")

    def play_midi_data_from_file(self, midi_file: mido.MidiFile) -> None:
        """MIDIファイルオブジェクトを演奏します。

        Args:
            midi_file (mido.MidiFile): MIDIファイルオブジェクト

        Raises:
            RuntimeError: 演奏エラーの場合
        """
        if self.is_playing:
            self.stop()

        self.is_playing = True

        # 別スレッドで演奏を開始
        self.play_thread = threading.Thread(target=self._play_midi_thread, args=(midi_file,))
        self.play_thread.daemon = True
        self.play_thread.start()

    def _play_midi_thread(self, midi_file: mido.MidiFile) -> None:
        """MIDIファイルを演奏するスレッド関数。

        Args:
            midi_file (mido.MidiFile): MIDIファイルオブジェクト
        """
        try:
            if not self.midi_out:
                raise RuntimeError("MIDI出力が初期化されていません")

            # 全てのトラックを統合して演奏
            for msg in midi_file.play():
                if not self.is_playing:
                    break

                # メタメッセージ以外のMIDIメッセージを送信
                if not msg.is_meta:
                    self.midi_out.send_message(msg.bytes())

                # 必要に応じて待機
                if hasattr(msg, "time") and msg.time > 0:
                    time.sleep(msg.time)

            # 演奏終了後、全ての音を停止
            self._send_all_notes_off()

        except Exception as e:
            print(f"MIDI演奏中にエラーが発生しました: {str(e)}")
        finally:
            self.is_playing = False

    def _send_all_notes_off(self) -> None:
        """全てのチャンネルで全ての音符をオフにします。"""
        try:
            if self.midi_out:
                # 全チャンネルでAll Notes Offを送信
                for channel in range(16):
                    # All Notes Off (CC 123)
                    all_notes_off = [0xB0 + channel, 123, 0]
                    self.midi_out.send_message(all_notes_off)

                    # All Sound Off (CC 120)
                    all_sound_off = [0xB0 + channel, 120, 0]
                    self.midi_out.send_message(all_sound_off)
        except Exception as e:
            print(f"All Notes Off送信中にエラーが発生しました: {str(e)}")

    def stop(self) -> None:
        """演奏を停止します。"""
        self.is_playing = False

        # 演奏スレッドの終了を待機
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=1.0)

        # 全ての音を停止
        self._send_all_notes_off()

    def is_device_available(self, device_name: str) -> bool:
        """指定されたMIDIデバイスが利用可能かチェックします。

        Args:
            device_name (str): チェックするデバイス名

        Returns:
            bool: デバイスが利用可能な場合True
        """
        try:
            available_devices = self.get_available_devices()
            return any(device_name.lower() in device.lower() for device in available_devices)
        except Exception:
            return False

    def get_device_info(self) -> Dict[str, Any]:
        """現在のMIDIデバイス情報を取得します。

        Returns:
            Dict[str, Any]: デバイス情報
        """
        try:
            available_devices = self.get_available_devices()

            return {
                "current_device": self.device_name or "デフォルト",
                "available_devices": available_devices,
                "is_initialized": self.midi_out is not None,
                "is_playing": self.is_playing,
            }
        except Exception as e:
            return {
                "current_device": self.device_name or "デフォルト",
                "available_devices": [],
                "is_initialized": False,
                "is_playing": False,
                "error": str(e),
            }

    def __del__(self):
        """デストラクタ：リソースをクリーンアップします。"""
        try:
            self.stop()
            if self.midi_out:
                self.midi_out.close_port()
        except Exception:
            pass  # デストラクタでは例外を無視
