insta_scraper_ai/
├── .env
├── README.md
├── requirements.txt
├── main.py
├── config/
│   └── settings.py
├── core/
│   ├── browser.py
│   └── scraper.py
├── ai/
│   └── extractor.py
├── data/
│   ├── raw/
│   └── processed/
├── logs/
├── utils/
│   └── helpers.py
├── tests/
│   └── test_scraper.py


| Folder/File        | Purpose                                                    |
| ------------------ | ---------------------------------------------------------- |
| `main.py`          | Entry point of the app                                     |
| `config/`          | Stores config like login credentials, selectors            |
| `core/`            | Playwright browser and scraping logic                      |
| `ai/`              | AI logic (e.g., profile classification, entity extraction) |
| `data/raw/`        | Stores raw HTML or JSON dumps                              |
| `data/processed/`  | Cleaned and structured data                                |
| `logs/`            | Runtime logs                                               |
| `utils/`           | Helper functions, decorators, etc.                         |
| `tests/`           | Unit tests for components                                  |
| `.env`             | Environment variables (like credentials)                   |
| `requirements.txt` | Python dependencies                                        |
