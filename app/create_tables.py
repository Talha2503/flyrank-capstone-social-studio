from app.database import engine, Base
from app import models

def main():
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    main()