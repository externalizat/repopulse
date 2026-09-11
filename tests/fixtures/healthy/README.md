# Healthy fixture

## Features

This small fixture represents a documented local Python project. It exists to
verify that RepoPulse can recognize a repository with the expected onboarding
materials. The application has one source file and a small test suite. Contributors
can inspect the implementation without setting up any external services or creating
accounts. All dependencies are declared in the requirements file with explicit
versions so that this fixture exercises the version declaration check as well.

## Installation

Install Python and run `pip install -r requirements.txt` in a virtual environment.

## Usage

Run `python src/app.py`. Run `pytest` to execute the tests. See the contributor
guide for the review workflow and the changelog for development history.
