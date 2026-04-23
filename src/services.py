def load_services():
    with open("services.txt") as f:
        return [line.strip() for line in f if line.strip()]
