---
hide:
  - toc
---

# Phase 1 Brief: Data Pipeline

**Status: Built and tested.** Steps 1 to 4 are done, and the 3 tests pass. The numbers below are the ones the code produces.

Phase 1 gets the data into the cloud and back. It downloads a public file of NFL game results, cleans it, keeps the cleaned copy in Amazon S3, and downloads that copy so every later step starts from the S3 version. It builds no features and trains nothing. Those start in [Phase 2](../phase-2/brief.md).

## Steps in Order

- [x] **Step 1. Fetch the raw data and save it.** `src/data/fetch_raw.py` saves the nflverse file unchanged as `data/raw/games.csv`.
- [x] **Step 2. Clean it and save the cleaned table.** `src/data/clean.py` writes `data/processed/nfl_matchups_2020_2026.csv`.
- [x] **Step 3. Upload the cleaned table to S3.** `src/data/upload_to_s3.py`, into the private bucket created manually.
- [x] **Step 4. Download it from S3 and save a local copy.** `src/data/download_from_s3.py` writes `data/from-s3/nfl_matchups_2020_2026.csv`.

## Results

- **Games kept:** 1,759, from the 2020 season through week 10 of 2026.
- **Cleaned table:** 7 columns, 63,908 bytes.
- **Cloud copy:** one object of the same size in a private S3 bucket.
- **Tests:** all pass, using made-up data and a fake S3 client. None call AWS.

## Where to Read More

- [Implementation](./implementation.md) explains how each step works, what was created, and why the choices were made.
- [Development Guide](./development-guide.md) shows how to run the four steps, change the pipeline, and check the cloud storage.
