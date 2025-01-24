from lmnr import Laminar as L
from lmnr import observe

L.initialize(project_api_key=os.getenv("LMNR_PROJECT_API_KEY"))


@observe()
def main():
    print("Hello from genai!")


if __name__ == "__main__":
    main()
