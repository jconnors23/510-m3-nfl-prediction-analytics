---
hide:
  - toc
---

# Phase 1 Synopsis: Data Pipeline

**Status: Being rebuilt.** This page describes the target. The old build is being undone and rebuilt from these pages, and the numbers here are the ones the rebuild must reproduce. The build instructions are in `specs/phase-1-rebuild-spec.md`.

Phase 1 gets the data into the cloud and back. It downloads a public file of NFL game results, cleans it, keeps the cleaned copy in Amazon S3, and downloads that copy so every later step starts from the S3 version. It builds no features and trains nothing. Those start in [Phase 2](../phase-2/synopsis.md).

## Requirements This Phase Covers

Each requirement is copied word for word from the [Project Requirements](../../initial-requirements/requirements.md), followed by what Phase 1 does about it.

- ☐ **Pick a public dataset (for example from Kaggle, UCI, or Hugging Face Datasets).** The nflverse `games.csv` file, one row per NFL game since 1999: [github.com/nflverse/nfldata](https://github.com/nflverse/nfldata/blob/master/data/games.csv).
- ☐ **Define a single supervised learning task: either classification or regression.** Binary classification: did the home team win (1) or not (0)? See [What Is the Prediction Task?](./implementation-details.md#what-is-the-prediction-task).
- ☐ **Clean and preprocess the dataset locally before uploading.** `src/data/clean.py` keeps 1,759 regular-season games that had a winner and saves 7 of the 46 columns. See [Step 2](./implementation-details.md#step-2-clean-the-raw-data-and-save-the-cleaned-table).
- ☐ **Upload the cleaned data to an Amazon S3 bucket. S3 is the chosen storage service for this project.** Upload to the private bucket `510-m3-nfl-dataset` in `us-east-1`.
- ☐ **Include a script that downloads the data from S3 programmatically (for example with boto3), so the pipeline starts from the S3 copy rather than a local file.** `src/data/download_from_s3.py` saves the S3 copy as `data/from-s3/nfl_matchups_2020_2026.csv`.
- ☐ **`config.yaml` for pipeline configuration.** `config/config.yaml` holds the paths, bucket, region, and season window. Every script reads it.
- ☐ **A dependency file: `requirements.txt` or `environment.yaml`.** `requirements.txt` pins every package to an exact version.

## Steps in Order

- [ ] **Step 1. Fetch the raw data and save it.** `src/data/fetch_raw.py` saves the nflverse file unchanged as `data/raw/games.csv`.
- [ ] **Step 2. Clean it and save the cleaned table.** `src/data/clean.py` writes `data/processed/nfl_matchups_2020_2026.csv`.
- [ ] **Step 3. Upload the cleaned table to S3.** `src/data/upload_to_s3.py`, into the private bucket created by hand.
- [ ] **Step 4. Download it from S3 and save a local copy.** `src/data/download_from_s3.py` writes `data/from-s3/nfl_matchups_2020_2026.csv`.

## Results the Rebuild Must Match

- **Games kept:** 1,759, from the 2020 season through week 10 of 2026.
- **Cleaned table:** 7 columns, 63,908 bytes.
- **Cloud copy:** one object of the same size in a private S3 bucket.
- **Tests:** all pass, using made-up data and a fake S3 client. None call AWS.

## Where to Read More

[Implementation Details](./implementation-details.md) explains how each step works, what was created, and why the choices were made.
