"""
MCPサーバーのテスト
"""

import json
from unittest.mock import patch

from src.mcp_server import MCPServer


def test_mcp_server_initialization():
    """MCPサーバーの初期化をテストします"""
    server = MCPServer()
    assert server.tools == {}
    assert server.tool_handlers == {}


def test_register_tool():
    """ツールの登録をテストします"""
    server = MCPServer()

    # テスト用のハンドラ関数
    def test_handler(params):
        return {"result": "test"}

    # ツールを登録
    server.register_tool(
        name="test_tool",
        description="Test tool",
        input_schema={
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
            },
            "required": ["param1"],
        },
        handler=test_handler,
    )

    # ツールが登録されていることを確認
    assert "test_tool" in server.tools
    assert "test_tool" in server.tool_handlers
    assert server.tools["test_tool"]["name"] == "test_tool"
    assert server.tools["test_tool"]["description"] == "Test tool"
    assert server.tool_handlers["test_tool"] == test_handler


@patch("sys.stdout")
def test_send_response(mock_stdout):
    """レスポンスの送信をテストします"""
    server = MCPServer()

    # レスポンスを送信
    response = {"jsonrpc": "2.0", "result": "test", "id": 1}
    server._send_response(response)

    # 標準出力に正しいJSONが出力されていることを確認
    # 注: 実装によっては、writeが2回呼ばれる場合があります（JSONと改行を別々に書き込む場合）
    mock_stdout.write.assert_any_call(json.dumps(response))
    mock_stdout.flush.assert_called_once()


@patch("src.mcp_server.MCPServer._send_result")
def test_handle_tools_call(mock_send_result):
    """tools/callメソッドの処理をテストします"""
    server = MCPServer()

    # テスト用のハンドラ関数
    def test_handler(params):
        return {"content": [{"type": "text", "text": f"Result: {params.get('param1')}"}]}

    # ツールを登録
    server.register_tool(
        name="test_tool",
        description="Test tool",
        input_schema={
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
            },
            "required": ["param1"],
        },
        handler=test_handler,
    )

    # tools/callメソッドを呼び出し
    params = {
        "name": "test_tool",
        "arguments": {
            "param1": "test_value",
        },
    }
    server._handle_tools_call(params, 1)

    # _send_resultが正しく呼び出されていることを確認
    mock_send_result.assert_called_once_with({"content": [{"type": "text", "text": "Result: test_value"}]}, 1)


@patch("src.mcp_server.MCPServer._send_result")
def test_handle_tools_call_error(mock_send_result):
    """tools/callメソッドのエラー処理をテストします"""
    server = MCPServer()

    # テスト用のハンドラ関数（例外を発生させる）
    def test_handler(params):
        raise ValueError("Test error")

    # ツールを登録
    server.register_tool(
        name="test_tool",
        description="Test tool",
        input_schema={
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
            },
            "required": ["param1"],
        },
        handler=test_handler,
    )

    # tools/callメソッドを呼び出し
    params = {
        "name": "test_tool",
        "arguments": {
            "param1": "test_value",
        },
    }
    server._handle_tools_call(params, 1)

    # _send_resultが正しく呼び出されていることを確認
    mock_send_result.assert_called_once()
    args, _ = mock_send_result.call_args
    assert args[0]["isError"] is True
    assert "Test error" in args[0]["content"][0]["text"]


@patch("src.mcp_server.MCPServer._send_result")
def test_handle_notifications_initialized(mock_send_result):
    """notifications/initializedメソッドの処理をテストします"""
    server = MCPServer()

    # notifications/initializedメソッドを呼び出し（request_idありの場合）
    server._handle_notifications_initialized({}, 1)

    # _send_resultが正しく呼び出されていることを確認
    mock_send_result.assert_called_once_with({}, 1)


def test_handle_notifications_initialized_no_response():
    """notifications/initializedメソッドの処理をテストします（応答不要の場合）"""
    server = MCPServer()

    # notifications/initializedメソッドを呼び出し（request_idなしの場合）
    # 例外が発生しないことを確認
    server._handle_notifications_initialized({}, None)


@patch("src.mcp_server.MCPServer._send_result")
def test_handle_resources_list(mock_send_result):
    """resources/listメソッドの処理をテストします"""
    server = MCPServer()

    # resources/listメソッドを呼び出し
    server._handle_resources_list({}, 1)

    # _send_resultが正しく呼び出されていることを確認
    mock_send_result.assert_called_once_with({"resources": []}, 1)


@patch("src.mcp_server.MCPServer._send_result")
def test_handle_resources_templates_list(mock_send_result):
    """resources/templates/listメソッドの処理をテストします"""
    server = MCPServer()

    # resources/templates/listメソッドを呼び出し
    server._handle_resources_templates_list({}, 1)

    # _send_resultが正しく呼び出されていることを確認
    mock_send_result.assert_called_once_with({"resourceTemplates": []}, 1)


def test_get_resource_templates():
    """_get_resource_templatesメソッドをテストします"""
    server = MCPServer()

    # リソーステンプレートの一覧を取得
    resource_templates = server._get_resource_templates()

    # 空のリストが返されることを確認
    assert resource_templates == []
