# RAT-Rotational-Angular-Tracking

## Project description

Desktop computer-vision tool for tracking rotational/angular behavior and classifying observed activity.

## Architecture

`main.py` provides the application entry; `tracker.py` performs tracking; `classifier.py` classifies observations; `installer.py` and platform scripts package and launch the app; supporting images and ethogram data document the workflow.

## Technology

Python • Computer Vision • desktop packaging

## Run locally

Install `requirements.txt`, then run `python main.py`.

## Repository guide

The implementation is organized so that entry points remain thin and domain-specific logic stays in the modules named above. Configuration, assets, and deployment files are kept separate from application code. Review the source tree before changing behavior, and keep secrets in local environment files rather than committing them.
