# RSM2303H

## Risk Modelling and Financial Trading Strategy

## About Laptop Setup

- Assuming you are using **MacOS**
- Assuming you have **VSCode** or any modern code editor
- For best coding experience:
  - Install **pre-commit**:
    ```sh
    brew install pre-commit
    ```
    Check installation:
    ```sh
    pre-commit --version
    ```
  - Install **Poetry**:
    ```sh
    brew install poetry
    ```
    Check installation:
    ```sh
    poetry --version
    ```

## Setup and Installation

### Clone the Repository
```sh
git clone https://github.com/mayureshucsb2019/RSM2303H.git
cd RSM2303H
```

### To Create the Folder Structure (Already Formatted)

- Ensure `poetry` is installed on your local machine
- Run:
  ```sh
  poetry new trading_strategies
  ```
- Rename the outer folder to `_RSM2303H_`
- Add a **.env** file with your own credentials

### Install Dependencies
Using **Poetry**:
```sh
poetry install
```

## Running the Project
Run the project using:
```sh
poetry run python <relative_path_to_your_file>
```

## Running Tests
To run tests, use:
```sh
poetry run pytest
```

For coverage:
```sh
poetry run pytest --cov=your_project_directory
```

## Linting and Formatting
Ensure code quality by running:
```sh
poetry run flake8 .
poetry run black .
```

## Instructions When Committing Code to the Repo
Run:
```sh
pre-commit run --all-files
```

## Troubleshooting
- If you see **Pylance warnings** in VS Code about missing imports, ensure the correct Poetry environment is selected.
- If **Poetry install fails**, try:
  ```sh
  poetry lock --no-update
  poetry install
  ```

## Contributing
Feel free to submit **issues** or **pull requests** to improve the project.

## License
[Specify your project's license here]

