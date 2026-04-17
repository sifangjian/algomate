from src.algomate.main import AlgomateApp

if __name__ == "__main__":
    app = AlgomateApp()
    app.start_review_scheduler()
    print("Algomate started successfully!")
