

1. Clone the project in VS Code, PyCharm or other Python IDE from GitHub
2. The building-heat code has the following structure:

    ```text

   ├── .gitignore                  # Git ignore file
   ├── README.md                   # Project instructions and setup
   ├── requirements.txt            # List of dependencies
   ├── pyproject.toml              # Installation and package metadata
   ├── .env                        # Contains Guardian API key (not tracked by Git)
   ├── src/
   │   ├── leet_app/               # Main Flask application
   │   │   ├── __init__.py         # Flask factory and blueprint registration
   │   │   ├── routes.py           # All route logic (visualisations, reports, ESG)
   │   │   ├── models.py           # SQLAlchemy ORM models
   │   │   ├── forms.py            # Flask-WTF forms and validation
   │   │   ├── figures.py          # Chart generation with Plotly
   │   │   ├── report_utils.py     # Data logic for report generation and exports
   │   │   ├── add_data.py         # Loads and preprocesses CSV data
   |   |   ├── extensions.py  
   │   │   ├── run.py              # Optional run script
   │   │   ├── templates/          # Jinja HTML templates
   │   │   └── static/             # CSS, images, JS
   ├── tests/
   │   ├── conftest.py             # Fixtures and test configuration
   │   ├── test_forms.py           # Unit tests for Flask-WTF forms
   │   ├── test_models.py          # SQLAlchemy model tests
   │   ├── test_routes.py          # Flask test client route tests
   │   ├── test_integration.py     # Selenium WebDriver integration tests
   └── data/
      └── prepared_heat_demand_data.csv  # Energy dataset used in setup

      ```
3. Create and activate a virtual environment e.g. `.venv`
4. Install the project code using `pip install -e .`.

   If you use this command you should not also need to use the `requirements.txt` file. If this step fails, then install
   the required packages by entering `pip install -r requirements.txt` in the IDE's terminal window.

5. The /esg route retrieves real-time energy-related articles using The Guardian Open Platform.
	To enable this feature:
	Register for a free API key: https://open-platform.theguardian.com
	Create a .env file in the root project directory (same level as README.md) with the following content:
            GUARDIAN_API_KEY=your-api-key-here
   Terms of Use: This application uses the Guardian API for non-commercial, educational purposes in accordance with The Guardian’s Open Platform terms.
   If you are marking this coursework, you may also have access to my own API which is included in the coursework2 pdf report. 

6. Run the full suite of test using the following command `pytest` in the termina.  These should pass if your project files are structured as above and you completed
   `pip install -e .` To run individual test modules:
   Run  `pytest -v tests/test_forms.py`to run unit tests of Flask-wtf forms.
   Run  ` pytest -v tests/test_integration.py`to run integration testing with Selenium Driver.
   Run  `pytest -v tests/test_models.py`to run unit tests of SQLAlchemy models.
   Run  `pytest -v tests/test_routes.py`to test routes using Flask test client.

7. Run the Flask app from the terminal using `flask --app leet_app run --debug`.

   You’ll see output similar to this:

    ```text
   * Serving Flask app "leet_app"
   * Debug mode: on
   * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
   * Restarting with stat
   * Debugger is active!
   * Debugger PIN: nnn-nnn-nnn
   ```

   Visit http://127.0.0.1:5000/ in a browser, and you should see the home page of the app.

   If another program is already using port 5000, you’ll see OSError: `[Errno 98]` or OSError: `[WinError 10013]` when
   the server tries to start.
   You can specify a different port using `--port` e.g.  `flask --app flaskstarter run --debug --port 5001`

You can also run the Flask app using `run.py` using the green run button in your IDE, or `python src/leet_app/run.py`.


