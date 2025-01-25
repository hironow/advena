import os

import weave
from lmnr import Laminar as L
from lmnr import observe


@weave.op()
@observe()
def main():
    print("Hello from genai!")


if __name__ == "__main__":
    weave.init(project_name=os.getenv("WEAVE_PROJECT_NAME"))
    L.initialize(project_api_key=os.getenv("LMNR_PROJECT_API_KEY"))

    main()
