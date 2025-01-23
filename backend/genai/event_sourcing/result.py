from typing import Generic, TypeVar

TSuccess = TypeVar("TSuccess")
TFailure = TypeVar("TFailure")


class Ok(Generic[TSuccess]):
    """成功を表すクラス"""

    __match_args__ = ("value",)

    def __init__(self, value: TSuccess):
        self.value = value

    def __repr__(self):
        return f"Ok({self.value})"


class Error(Generic[TFailure]):
    """失敗を表すクラス"""

    __match_args__ = ("value",)

    def __init__(self, value: TFailure):
        self.value = value

    def __repr__(self):
        return f"Error({self.value})"


# Result型:
# 例外を型によって提供する Result型 と 発生する Error型 を提供する。これにより raise は禁止される
#
# type Result<'Success,'Failure> =
#   | Ok of 'Success
#   | Error of 'Failure
# に相当する
Result = Ok[TSuccess] | Error[TFailure]


if __name__ == "__main__":

    def divide(a: float, b: float) -> Result[float, str]:
        if b == 0:
            return Error("Cannot divide by zero.")
        else:
            return Ok(a / b)

    # 実際に使ってみる
    r1 = divide(10, 2)
    r2 = divide(5, 0)

    print(r1)  # Ok(5.0)
    print(r2)  # Error(Cannot divide by zero.)

    # 値を取り出す例
    # if文で取り出す
    if isinstance(r1, Ok):
        print("Success:", r1.value)  # 5.0
    elif isinstance(r1, Error):
        print("Failure:", r1.value)

    # matchで取り出す (推奨)
    match r2:
        case Ok(value):
            print("Success:", value)
        case Error(value):
            print("Failure:", value)  # Cannot divide by zero.
