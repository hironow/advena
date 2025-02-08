from typing import Any

from sickle import Sickle  # type: ignore

from .book import JPRO_REPOSITORY, OAI_PMH_URL_BASE

sickle_client = Sickle(OAI_PMH_URL_BASE)


def get_metadata_by_isbn(
    isbn: str, repository: str = JPRO_REPOSITORY
) -> dict[str, Any]:
    """OAI-PMH で書誌情報を取得する

    例: https://ndlsearch.ndl.go.jp/api/oaipmh?verb=GetRecord&metadataPrefix=dcndl&identifier=oai:ndlsearch.ndl.go.jp:R100000137-I9784621310328
    """
    # ハイフンがあれば取り除く
    isbn = isbn.replace("-", "")
    # ISBN は 13 桁でハイフン区切りなし。NOTE: JP-eコードは 20 桁で区切りなしだが、ここでは ISBN のみを想定する
    if len(isbn) != 13:
        raise ValueError("ISBN should be 13 digits")

    # TODO: identifierを引数にする
    identifier = f"oai:ndlsearch.ndl.go.jp:{repository}-I{isbn}"
    # dcndl が情報が多いのでそちらを利用
    record = sickle_client.GetRecord(metadataPrefix="dcndl", identifier=identifier)
    metadata = record.metadata
    print(type(metadata))
    return metadata


if __name__ == "__main__":
    isbn = "9784621310328"
    get_metadata_by_isbn(isbn)
