# RSM2303H

Risk Modelling and Financial Trading Strategy

# About laptop setup

- assuming you are using MacOS
- assuming you have VSCode or any modern code editor
- For best coding experience:
  - you have pre-commit installed `$ brew install pre-commit` check using `$  pre-commit --version`
  - you have poetry installed `$ brew install poetry`check using `$ poetry --version`

# To create the folder structure (already formatted)

- You need to install `poetry` in you local machine
- Run `$ poetry new trading_strategies`
- Rename the outer folder to _RSM2303H_

Note: Add a _.env_ file with your own credentials

# To run the project

- Run `$ poetry run python <relative_path_to_your_file>`

# To run the tests

- Run `$ poetry run pytest`

# Instructions when commiting the code to the repo

- Run `$ pre-commit run --all-files`
