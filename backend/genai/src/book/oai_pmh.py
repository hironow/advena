from typing import Any

from ratelimit import limits
from sickle import Sickle
from sickle.oaiexceptions import OAIError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .book import JPRO_REPOSITORY, OAI_PMH_URL_BASE

sickle_client = Sickle(OAI_PMH_URL_BASE)


# 例: 1分間に最大60回の呼び出し（1秒に1回）に制限
CALLS = 120
PERIOD = 60  # 秒


@limits(calls=CALLS, period=PERIOD)
@retry(
    wait=wait_exponential(
        multiplier=1, min=2, max=60
    ),  # 失敗時は最初2秒、最大60秒まで待機
    stop=stop_after_attempt(5),  # 最大5回までリトライ
    retry=retry_if_exception_type(OAIError),  # OAIError が発生したらリトライ
)
def _get_metadata_by_identifier(repository: str, identifier: str) -> dict[str, Any]:
    if repository == "" or identifier == "":
        raise ValueError("repository and identifier should not be empty")
    identifier = f"oai:ndlsearch.ndl.go.jp:{repository}-I{identifier}"
    # dcndl が情報が多いのでそちらを利用
    record = sickle_client.GetRecord(metadataPrefix="dcndl", identifier=identifier)  # type: ignore
    metadata = record.metadata  # type: ignore
    return metadata  # type: ignore


def get_metadata_by_isbn(
    isbn: str, repository: str = JPRO_REPOSITORY
) -> dict[str, Any]:
    """OAI-PMH をISBNで書誌情報を取得する (JPROを想定)
    例: https://ndlsearch.ndl.go.jp/api/oaipmh?verb=GetRecord&metadataPrefix=dcndl&identifier=oai:ndlsearch.ndl.go.jp:R100000137-I9784621310328
    """
    isbn = isbn.replace("-", "")
    if len(isbn) != 13:
        raise ValueError("ISBN should be 13 digits")

    return _get_metadata_by_identifier(repository, isbn)


def get_metadata_by_jp_e_code(
    jp_e_code: str, repository: str = JPRO_REPOSITORY
) -> dict[str, Any]:
    """OAI-PMH をjp_e_codeで書誌情報を取得する (JPROを想定)
    例: https://ndlsearch.ndl.go.jp/api/oaipmh?verb=GetRecord&metadataPrefix=dcndl&identifier=oai:ndlsearch.ndl.go.jp:R100000137-I09D154490010d0000000
    """
    jp_e_code = jp_e_code.replace("-", "")
    if len(jp_e_code) != 20:
        raise ValueError("JP-eCode should be 20 digits")
    return _get_metadata_by_identifier(repository, jp_e_code)


if __name__ == "__main__":
    isbn = "9784621310328"
    get_metadata_by_isbn(isbn)

    jp_e_code = "09D154490010d0000000"
    get_metadata_by_isbn(jp_e_code)
