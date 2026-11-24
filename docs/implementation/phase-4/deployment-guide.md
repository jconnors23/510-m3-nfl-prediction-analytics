---
hide:
  - toc
---

# Phase 4 Deployment Guide

This guide holds every AWS command for the Phase 4 API, in order: deploy it, redeploy it, change its settings, and remove it. Each step is explained in the [Phase 4 Implementation](./implementation.md). To test the entry point with no AWS account, or change its code, see the [Development Guide](./development-guide.md).

## How Do the Sections Fit Together?

```mermaid
flowchart TB
    subgraph Local["On this computer"]
        A["Build the Zip<br/>installed packages + project files"]
    end
    subgraph AWS["On AWS (us-east-1)"]
        B["Check the Account<br/>and that the names are free"] --> C["Create the Role<br/>logs only"]
        C --> D["Stage the Zip in S3<br/>and Create the Function"]
        D --> E["Create the HTTP API<br/>routes, permission, CORS"]
        E --> F["Check the public address"]
    end
    A --> B
    F --> G["Check the Deployed Model<br/>Against the Local Model"]
    G -.-> R["Redeploy After a Change<br/>(later changes)"]
    G -.-> S["Change a Setting<br/>or the CORS List"]
    G -.-> H["Remove Everything<br/>(written, not run)"]
```

- **Build the Zip** runs on this computer and calls no AWS service.
- **Check the Account** confirms the right account and that no resource with a name from this guide exists yet.
- **Create the Role**, **Stage the Zip and Create the Function**, and **Create the HTTP API** create the AWS resources, in that order, because each needs the one before it.
- **Check the Deployed Model Against the Local Model** proves the function runs the zip built here and gives the same answers as the local model.
- **Redeploy After a Change**, **Change a Setting Without New Code**, and **Change the CORS List** are for later changes to the running deployment.
- **Remove Everything** deletes what this guide created. The commands are written and are not run as part of the deployment.

Run these from the project folder, in order. Resource names stay as written. `<account-id>`, `<api-id>`, and `<integration-id>` stand in for values that differ between accounts.

About the settings: memory is 1769 MB and was left untuned. `JOBLIB_MULTIPROCESSING=0` stops a harmless joblib warning about multiprocessing, which Lambda does not provide.

Before the first command:

- AWS CLI 2.35.9 is installed, and the default credentials can reach the account that owns `510-m3-nfl-dataset` in `us-east-1`.
- The project virtual environment is Python 3.13.14.
- `models/model.joblib` exists and was saved by scikit-learn 1.9.1.
- `requirements-serve.txt` and `src/api/lambda_handler.py` exist.

## Build the Zip

1. Remove the previous build folder and zip.

```bash
rm -rf build/lambda build/510-m3-nfl-predict-api.zip
```

2. Install the serving packages for Linux arm64 and Python 3.13.

```bash
.venv/bin/python -m pip install --target build/lambda --implementation cp --python-version 3.13 --platform manylinux_2_28_aarch64 --platform manylinux2014_aarch64 --only-binary=:all: --no-compile -r requirements-serve.txt
```

3. Delete cached bytecode from the build.

```bash
find build/lambda -type d -name __pycache__ -prune -exec rm -rf {} +
```

4. Copy the project files the function imports, keeping the folder layout.

```bash
mkdir -p build/lambda/src/api build/lambda/config build/lambda/models
```

```bash
cp src/config.py build/lambda/src/config.py
```

```bash
cp src/api/app.py src/api/lambda_handler.py src/api/schemas.py build/lambda/src/api/
```

```bash
cp config/config.yaml build/lambda/config/config.yaml
```

```bash
cp models/model.joblib build/lambda/models/model.joblib
```

5. Zip the contents of `build/lambda`, so `src/`, `config/`, and `models/` sit at the top.

```bash
(cd build/lambda && zip -r -q ../510-m3-nfl-predict-api.zip .)
```

## Check the Account

6. Confirm the caller and the data bucket. The bucket command prints nothing when the bucket is reachable.

```bash
aws sts get-caller-identity --region us-east-1
```

```bash
aws s3api head-bucket --bucket 510-m3-nfl-dataset --region us-east-1
```

7. Confirm the names are free. A missing function, role, or zip is the expected result. The API query should print `0`.

```bash
aws lambda get-function --function-name 510-m3-nfl-predict-api --region us-east-1
```

```bash
aws iam get-role --role-name 510-m3-nfl-predict-api-role --region us-east-1
```

```bash
aws apigatewayv2 get-apis --region us-east-1 --query "length(Items[?Name=='510-m3-nfl-predict-http-api'])" --output text
```

```bash
aws s3api head-object --bucket 510-m3-nfl-dataset --key deploy/510-m3-nfl-predict-api.zip --region us-east-1
```

## Create the Role

8. Write the trust policy. It lets only Lambda assume the role. A statement id is omitted because IAM rejects a hyphenated id.

```bash
mkdir -p build
```

```bash
cat > build/trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
```

9. Create the role and attach the logs policy.

```bash
aws iam create-role --role-name 510-m3-nfl-predict-api-role --assume-role-policy-document file://build/trust-policy.json --tags Key=project,Value=510-m3 --region us-east-1
```

```bash
aws iam attach-role-policy --role-name 510-m3-nfl-predict-api-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole --region us-east-1
```

## Stage the Zip and Create the Function

10. Copy the zip into the data bucket.

```bash
aws s3 cp build/510-m3-nfl-predict-api.zip s3://510-m3-nfl-dataset/deploy/510-m3-nfl-predict-api.zip --region us-east-1
```

11. Create the function from that object. If this fails because the new role cannot be assumed yet, wait a few seconds and run it again, up to 5 times.

```bash
aws lambda create-function --function-name 510-m3-nfl-predict-api --runtime python3.13 --architectures arm64 --handler src.api.lambda_handler.handler --role arn:aws:iam::<account-id>:role/510-m3-nfl-predict-api-role --code S3Bucket=510-m3-nfl-dataset,S3Key=deploy/510-m3-nfl-predict-api.zip --memory-size 1769 --timeout 10 --environment "Variables={JOBLIB_MULTIPROCESSING=0}" --tags project=510-m3 --region us-east-1
```

12. Wait until the function is active.

```bash
aws lambda wait function-active --function-name 510-m3-nfl-predict-api --region us-east-1
```

13. Write the three test events. The predict event is the worked example. The health event has no body. The bad event sends only an out-of-range win percentage.

```bash
cat > build/predict-event.json <<'EOF'
{"version":"2.0","routeKey":"POST /predict","rawPath":"/predict","rawQueryString":"","headers":{"content-type":"application/json"},"requestContext":{"accountId":"123456789012","apiId":"test","domainName":"test.execute-api.us-east-1.amazonaws.com","http":{"method":"POST","path":"/predict","protocol":"HTTP/1.1","sourceIp":"127.0.0.1","userAgent":"test"},"requestId":"test","routeKey":"POST /predict","stage":"$default","time":"01/Jan/2026:00:00:00 +0000","timeEpoch":1767225600000},"body":"{\"win_pct_differential\": -0.5, \"point_diff_per_game_differential\": -18.0}","isBase64Encoded":false}
EOF
```

```bash
cat > build/health-event.json <<'EOF'
{"version":"2.0","routeKey":"GET /health","rawPath":"/health","rawQueryString":"","headers":{"content-type":"application/json"},"requestContext":{"accountId":"123456789012","apiId":"test","domainName":"test.execute-api.us-east-1.amazonaws.com","http":{"method":"GET","path":"/health","protocol":"HTTP/1.1","sourceIp":"127.0.0.1","userAgent":"test"},"requestId":"test","routeKey":"GET /health","stage":"$default","time":"01/Jan/2026:00:00:00 +0000","timeEpoch":1767225600000},"isBase64Encoded":false}
EOF
```

```bash
cat > build/bad-body-event.json <<'EOF'
{"version":"2.0","routeKey":"POST /predict","rawPath":"/predict","rawQueryString":"","headers":{"content-type":"application/json"},"requestContext":{"accountId":"123456789012","apiId":"test","domainName":"test.execute-api.us-east-1.amazonaws.com","http":{"method":"POST","path":"/predict","protocol":"HTTP/1.1","sourceIp":"127.0.0.1","userAgent":"test"},"requestId":"test","routeKey":"POST /predict","stage":"$default","time":"01/Jan/2026:00:00:00 +0000","timeEpoch":1767225600000},"body":"{\"win_pct_differential\": 1.5}","isBase64Encoded":false}
EOF
```

14. Invoke the worked example twice, then health, then the bad body. Add `--cli-binary-format raw-in-base64-out` on AWS CLI version 2.

```bash
aws lambda invoke --function-name 510-m3-nfl-predict-api --cli-binary-format raw-in-base64-out --payload file://build/predict-event.json --log-type Tail --region us-east-1 build/invoke-predict-1.json
```

```bash
aws lambda invoke --function-name 510-m3-nfl-predict-api --cli-binary-format raw-in-base64-out --payload file://build/predict-event.json --log-type Tail --region us-east-1 build/invoke-predict-2.json
```

```bash
aws lambda invoke --function-name 510-m3-nfl-predict-api --cli-binary-format raw-in-base64-out --payload file://build/health-event.json --log-type Tail --region us-east-1 build/invoke-health.json
```

```bash
aws lambda invoke --function-name 510-m3-nfl-predict-api --cli-binary-format raw-in-base64-out --payload file://build/bad-body-event.json --log-type Tail --region us-east-1 build/invoke-bad.json
```

15. Delete the staged zip and confirm the `deploy/` prefix is empty.

```bash
aws s3 rm s3://510-m3-nfl-dataset/deploy/510-m3-nfl-predict-api.zip --region us-east-1
```

```bash
aws s3api list-objects-v2 --bucket 510-m3-nfl-dataset --prefix deploy/ --region us-east-1
```

## Create the HTTP API

16. Create the API, one proxy integration, the two routes, and the `$default` stage.

```bash
aws apigatewayv2 create-api --name 510-m3-nfl-predict-http-api --protocol-type HTTP --tags project=510-m3 --region us-east-1
```

```bash
aws apigatewayv2 create-integration --api-id <api-id> --integration-type AWS_PROXY --integration-uri arn:aws:lambda:us-east-1:<account-id>:function:510-m3-nfl-predict-api --payload-format-version 2.0 --region us-east-1
```

```bash
aws apigatewayv2 create-route --api-id <api-id> --route-key 'POST /predict' --target integrations/<integration-id> --region us-east-1
```

```bash
aws apigatewayv2 create-route --api-id <api-id> --route-key 'GET /health' --target integrations/<integration-id> --region us-east-1
```

```bash
aws apigatewayv2 create-stage --api-id <api-id> --stage-name '$default' --auto-deploy --region us-east-1
```

17. Let this API invoke the function, and nothing broader. The statement id is `510-m3-nfl-predict-http-api`.

```bash
aws lambda add-permission --function-name 510-m3-nfl-predict-api --statement-id 510-m3-nfl-predict-http-api --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn arn:aws:execute-api:us-east-1:<account-id>:<api-id>/*/* --region us-east-1
```

18. Set CORS. Write the file, then apply it. At this step the only origin is `http://localhost:5173`. Phase 5 later adds the CloudFront address, with the commands in its [Deployment Guide](../phase-5/deployment-guide.md#add-the-cloudfront-address-to-the-apis-cors-list).

```bash
cat > build/cors.json <<'EOF'
{
  "AllowOrigins": ["http://localhost:5173"],
  "AllowMethods": ["POST", "GET", "OPTIONS"],
  "AllowHeaders": ["content-type"],
  "MaxAge": 300
}
EOF
```

```bash
aws apigatewayv2 update-api --api-id <api-id> --cors-configuration file://build/cors.json --region us-east-1
```

19. Tag the log group Lambda created.

```bash
aws logs tag-resource --resource-arn arn:aws:logs:us-east-1:<account-id>:log-group:/aws/lambda/510-m3-nfl-predict-api --tags project=510-m3 --region us-east-1
```

20. Keep the function's logs for 14 days.

```bash
aws logs put-retention-policy --log-group-name /aws/lambda/510-m3-nfl-predict-api --retention-in-days 14 --region us-east-1
```

21. Check the public address `https://<api-id>.execute-api.us-east-1.amazonaws.com`.

```bash
curl -sS -w '\nHTTP %{http_code}\n' https://<api-id>.execute-api.us-east-1.amazonaws.com/health
```

```bash
curl -sS -w '\nHTTP %{http_code}\n' -H 'content-type: application/json' -d '{"win_pct_differential": -0.5, "point_diff_per_game_differential": -18.0}' https://<api-id>.execute-api.us-east-1.amazonaws.com/predict
```

```bash
curl -sS -w '\nHTTP %{http_code}\n' -H 'content-type: application/json' -d '{"win_pct_differential": 1.5}' https://<api-id>.execute-api.us-east-1.amazonaws.com/predict
```

```bash
curl -sS -w '\nHTTP %{http_code}\n' https://<api-id>.execute-api.us-east-1.amazonaws.com/predict
```

```bash
curl -sS -o /dev/null -w 'HTTP %{http_code} time %{time_total}\n' https://<api-id>.execute-api.us-east-1.amazonaws.com/health
```

```bash
curl -sS -o /dev/null -w 'HTTP %{http_code} time %{time_total}\n' https://<api-id>.execute-api.us-east-1.amazonaws.com/health
```

```bash
curl -sS -D - -o /dev/null -X OPTIONS https://<api-id>.execute-api.us-east-1.amazonaws.com/predict -H 'Origin: http://localhost:5173' -H 'Access-Control-Request-Method: POST' -H 'Access-Control-Request-Headers: content-type'
```

```bash
curl -sS -D - -o /dev/null -X OPTIONS https://<api-id>.execute-api.us-east-1.amazonaws.com/predict -H 'Origin: http://example.com' -H 'Access-Control-Request-Method: POST' -H 'Access-Control-Request-Headers: content-type'
```

## Check the Deployed Model Against the Local Model

These checks confirm the function is running the zip built here, and that every game gets the same answer as the local model. The deployed zip is 63,452,500 bytes, with the hash `IU5bJH9pTL+rF/uEXMUAp+Eo/mik2abfaSasBXPOgbk=`. A later rebuild (made in Phase 7 and not deployed) came to 63,452,901 bytes, so a new zip will not match these two values. After a redeploy, compare the new zip's hash with `CodeSha256` instead. Both copies of the model hash to `8fff766505a925218eae2484ae56a8ba7baed06b62ce3413ea33c8eb15e8ea4b`. The data file hashes to `7219e8a8672b900af9facbb54d8a28f9f2a34df9ede3b8385a735768082517fb`, the same value as `data_sha256` in `results/run-summary.json`.

```bash
openssl dgst -sha256 -binary build/510-m3-nfl-predict-api.zip | base64
```

```bash
wc -c < build/510-m3-nfl-predict-api.zip
```

```bash
shasum -a 256 models/model.joblib
```

```bash
shasum -a 256 build/lambda/models/model.joblib
```

```bash
shasum -a 256 data/from-s3/nfl_matchups_2020_2026.csv
```

```bash
aws lambda get-function-configuration --function-name 510-m3-nfl-predict-api --region us-east-1
```

```bash
.venv/bin/python scripts/checks/parity_check.py
```

The committed script `scripts/checks/parity_check.py` writes its results to `build/parity-results.json`. It builds the local answers with the saved model and `src.model.features`, then posts each game to the public `/predict` route one at a time. It sends 1,759 games and should print 0 retries, 1,759 status 200 answers, 1,759 exact picks, 1,759 exact probabilities, a largest difference of 0, and these correct counts: training 820 of 1,339, validation 171 of 271, test 88 of 149.

## Redeploy After a Change

```mermaid
flowchart TB
    A["Change the code, or retrain the model"] --> B["Run the tests"]
    B --> C["Build the zip"]
    C --> D["Copy the zip into the data bucket<br/>(deploy/ prefix)"]
    D --> E["Update the function's code"]
    E --> F["Wait until the update finishes"]
    F --> G["Invoke the three test events"]
    G --> H["Delete the staged zip"]
    H --> I["Compare the zip's hash with CodeSha256,<br/>check the public address,<br/>and check every game"]
```

The zip is over the console's 50 MB direct-upload limit, so it is staged in S3 first, as it was for the first deployment. These commands reuse the names and options of the first deployment. **`update-function-code` has not been run in this project yet,** because the first deployment used `create-function` with the same S3 object. Its parameters (`--s3-bucket` and `--s3-key`) were checked against the AWS CLI's parameter list.

1. Run the tests, then build the zip with [Build the Zip](#build-the-zip).
2. Copy the zip into the bucket:

```bash
aws s3 cp build/510-m3-nfl-predict-api.zip s3://510-m3-nfl-dataset/deploy/510-m3-nfl-predict-api.zip --region us-east-1
```

3. Point the function at it:

```bash
aws lambda update-function-code --function-name 510-m3-nfl-predict-api --s3-bucket 510-m3-nfl-dataset --s3-key deploy/510-m3-nfl-predict-api.zip --region us-east-1
```

4. Wait until the update finishes:

```bash
aws lambda wait function-updated --function-name 510-m3-nfl-predict-api --region us-east-1
```

5. Invoke the worked example, the health event, and the bad-body event, with the commands in step 14 of [Stage the Zip and Create the Function](#stage-the-zip-and-create-the-function).
6. Delete the staged zip, and confirm the prefix is empty:

```bash
aws s3 rm s3://510-m3-nfl-dataset/deploy/510-m3-nfl-predict-api.zip --region us-east-1
```

```bash
aws s3api list-objects-v2 --bucket 510-m3-nfl-dataset --prefix deploy/ --region us-east-1
```

7. Confirm Lambda runs the file you built. These two commands must print the same value:

```bash
aws lambda get-function-configuration --function-name 510-m3-nfl-predict-api --region us-east-1 --query CodeSha256 --output text
```

```bash
openssl dgst -sha256 -binary build/510-m3-nfl-predict-api.zip | base64
```

8. Check the public address and every game, with the commands in [Check the Deployed Model Against the Local Model](#check-the-deployed-model-against-the-local-model). Repeat this check whenever the model, the packages, or the API code change.

## Change a Setting Without New Code

The function's memory, timeout, and environment variable are settings, not code. Change one with `update-function-configuration`, then wait for the update to finish. For example, to set the memory:

```bash
aws lambda update-function-configuration --function-name 510-m3-nfl-predict-api --memory-size 1769 --region us-east-1
```

```bash
aws lambda wait function-updated --function-name 510-m3-nfl-predict-api --region us-east-1
```

- **Current values:** 1769 MB of memory, a 10-second timeout, and the one environment variable `JOBLIB_MULTIPROCESSING=0`. See [Step 5](./implementation.md#step-5-create-the-role-and-the-function).
- **`--environment` replaces every variable.** If you pass it, pass all of them together, for example `--environment "Variables={JOBLIB_MULTIPROCESSING=0}"`. Leave it out when you change only the memory.
- **Memory sets how much CPU the function gets, not what code it runs.** After any change, repeat the every-game check at the end of [Redeploy After a Change](#redeploy-after-a-change).

## Change the CORS List

CORS is set on the API Gateway, not in the app. The command replaces the whole setting, so `build/cors.json` must list every allowed origin:

```bash
aws apigatewayv2 update-api --api-id <api-id> --cors-configuration file://build/cors.json --region us-east-1
```

The `<api-id>` is the part of the public address before `.execute-api`. The deployed list allows two origins, `http://localhost:5173` and the Phase 5 CloudFront address `https://d1nubiunzfwm0q.cloudfront.net`, with the methods `POST`, `GET`, and `OPTIONS` and the header `content-type`. Any new file must list both origins, or the live page stops working. See [The Preflight](../phase-5/implementation-part-1.md#the-preflight).

## Remove Everything

These commands remove the AWS resources this deployment created. They were written and not run. The data bucket itself is not deleted. The staged zip is already gone; the `s3 rm` line is here in case a later run left it.

```bash
aws apigatewayv2 delete-api --api-id <api-id> --region us-east-1
```

```bash
aws lambda delete-function --function-name 510-m3-nfl-predict-api --region us-east-1
```

```bash
aws logs delete-log-group --log-group-name /aws/lambda/510-m3-nfl-predict-api --region us-east-1
```

```bash
aws iam detach-role-policy --role-name 510-m3-nfl-predict-api-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole --region us-east-1
```

```bash
aws iam delete-role --role-name 510-m3-nfl-predict-api-role --region us-east-1
```

```bash
aws s3 rm s3://510-m3-nfl-dataset/deploy/510-m3-nfl-predict-api.zip --region us-east-1
```

```bash
rm -rf build/lambda build/510-m3-nfl-predict-api.zip
```
