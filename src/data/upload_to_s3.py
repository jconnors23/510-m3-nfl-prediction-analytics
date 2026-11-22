"""Step 3: send the cleaned games table to S3.

The upload counts as done only when S3 reports an object of the same size as the local file.
"""

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.config import data_file, load_config


class SizeMismatchError(RuntimeError):
    """The object in S3 is not the same size as the file that was uploaded."""

    def __init__(self, local_size: int, remote_size: int):
        super().__init__(
            f"S3 object is {remote_size} bytes but the local file is {local_size} bytes"
        )


def upload(config: dict, client=None) -> None:
    """Upload the cleaned table, then confirm S3 holds a file of the same size."""
    bucket = config["data"]["s3_bucket"]

    path = data_file(config, "processed_path")
    if not path.is_file():
        raise ValueError(f"No cleaned table at {path}. Run the clean step first.")

    # Tests pass in a fake client. A real run builds one from the machine's AWS credentials.
    # boto3 finds your AWS credentials itself (environment variables or ~/.aws), so no key is
    # ever written in this project.
    if client is None:
        client = boto3.client("s3", region_name=config["data"]["aws_region"])
    # The key is the file's name inside the bucket, like a path inside a folder.
    key = config["data"]["s3_key"]
    client.upload_file(str(path), bucket, key)
    # Ask S3 how big the stored object is. This is the proof the upload finished.
    remote_size = int(client.head_object(Bucket=bucket, Key=key)["ContentLength"])

    local_size = path.stat().st_size
    # A size mismatch means the object in the bucket is not the file that was sent.
    if remote_size != local_size:
        raise SizeMismatchError(local_size, remote_size)
    print(f"uploaded {local_size} bytes to s3://{bucket}/{key}")


def main() -> None:
    """Command for Step 3: upload the cleaned table to S3."""
    try:
        upload(load_config())
    except (ClientError, BotoCoreError, SizeMismatchError, ValueError) as exc:
        # Expected problems end with a short message, not a traceback.
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    main()
