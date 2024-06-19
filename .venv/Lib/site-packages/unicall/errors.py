from typing import *  # type: ignore
from uniserde import Jsonable


# JSON-RPC Error Codes
JSONRPC_PARSE_ERROR = -32700  # Invalid JSON was received by the server
JSONRPC_INVALID_REQUEST = -32600  # The JSON sent is not a valid Request object
JSONRPC_METHOD_NOT_FOUND = -32601  # The method does not exist / is not available
JSONRPC_INVALID_PARAMS = -32602  # Invalid method parameter(s)
JSONRPC_INTERNAL_ERROR = -32603  # Internal JSON-RPC error
JSONRPC_SERVER_ERROR = -32000  # Reserved for implementation-defined server-errors


class RpcError(Exception):
    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[int] = None,
        error_data: Optional[Jsonable] = None,
        debug_object: Any = None,
    ):
        super().__init__(message, error_code, error_data, debug_object)

    @property
    def message(self) -> str:
        return self.args[0]

    @property
    def error_code(self) -> Optional[int]:
        return self.args[1]

    @property
    def error_data(self) -> Optional[Jsonable]:
        return self.args[2]

    @property
    def debug_object(self) -> Any:
        return self.args[3]

    def as_jsonrpc_response_message(
        self, message_id: Union[None, int, str]
    ) -> Jsonable:
        result = {
            "jsonrpc": "2.0",
            "error": {
                "code": JSONRPC_SERVER_ERROR
                if self.error_code is None
                else self.error_code,
                "message": self.message,
            },
            "id": message_id,
        }

        if self.error_data is not None:
            result["error"]["data"] = self.error_data

        return result
