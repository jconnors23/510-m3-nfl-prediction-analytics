---
hide:
  - toc
---

# Glossary

This page explains every term used in the architecture overview and the five phase guides, in plain words. The terms are grouped by topic, starting with the football, then the data, the model, the tools, and the AWS services. The "Used in" column names the phase where a term matters most.

## Which Football Terms Does the Project Use?

| Term | What it means | Used in |
| :--- | :--- | :--- |
| NFL | The National Football League, the top professional American football league. It has 32 teams. | All phases |
| Regular season | The scheduled games played before the playoffs. The project uses only these games. From 2021 on, each team plays 17 games over 18 weeks. Before 2021, each team played 16 games over 17 weeks. | Phase 1 |
| Playoffs | The knockout games after the regular season. The project leaves them out. | Phase 1 |
| Week | One round of the regular-season schedule. A team plays at most one game per week. | Phase 1 |
| Bye week | A week in which a team has no game. It gives that team extra rest. | Phase 1 |
| Kickoff | The start of a game. The model predicts before kickoff, using only what is known by then. | All phases |
| Home team and away team | The home team plays in its own stadium. The away team travels. | All phases |
| Home-field advantage | The tendency of home teams to win more often than away teams. In the 2016 to 2024 data, home teams won 54.75% of games that did not end in a tie. | Phase 1, Phase 2 |
| Tie | A game that ends level after overtime. The cleaned data has 9 ties in the training seasons. | Phase 1 |
| Point differential | Points a team scored minus points it allowed. The project uses the per-game average: the total divided by games played. | Phase 1 |
| Win percentage | Wins divided by games played. A tie counts as half a win. | Phase 1 |
| Rest days | The number of days since a team's previous game. | Phase 1, Phase 5 |
| Season-to-date | Counting only games from earlier weeks of the same season. This keeps the numbers honest for a pre-game prediction. | Phase 1 |
| Team code | A short abbreviation for a team, such as `KC` or `BAL`. The data still contains old codes `OAK` and `SD`, which the cleaning step maps to `LV` and `LAC`. | Phase 1 |
| Betting line | The odds or point spread set by sportsbooks. The source file contains them, but the model does not use them. | Overview |

## Which Data Terms Does the Project Use?

| Term | What it means | Used in |
| :--- | :--- | :--- |
| Dataset | A collection of data used for a project. Here it is one row for each NFL game. | Phase 1 |
| nflverse | An open community project that publishes NFL data. The project uses its `games.csv` file. | Phase 1 |
| CSV file | A plain text file where each line is a row and values are separated by commas. | Phase 1 |
| JSON | A plain text format for structured data, written as named fields in braces. The API and the team profiles file use it. | Phase 1, Phase 3 |
| Row | One record in a table. In the games table, one row is one game. | Phase 1 |
| Column | One named field in a table, such as `home_score`. | Phase 1 |
| Cleaning | Fixing or removing data so it is consistent: keeping the right games, mapping old team codes, and stopping on missing values. | Phase 1 |
| Preprocessing | Any preparation of data before a model sees it. Cleaning and feature building are both preprocessing. | Phase 1 |
| Feature | One input number the model uses to decide. This project has three. | Phase 1 |
| Feature engineering | Building features from raw columns. For example, turning scores and weeks into a season-to-date point differential. | Phase 1 |
| Differential | The home team's number minus the away team's number. A positive value favors the home team. | Phase 1 |
| Target | The answer the model tries to predict. Here it is `home_win`: 1 if the home team won, 0 if not. | Phase 1 |
| Label | A known answer for one row. The target column holds the label for each game. | Phase 1 |
| Data leakage | A feature that uses information from after the thing being predicted. It makes test scores look better than real use will be. Also called future information. | Phase 1 |
| pandas | A Python library for working with tables of data. | Phase 1 |
| NumPy | A Python library for fast number arrays. | Phase 1, Phase 3 |
| Team profiles file | A small file with each team's season-to-date numbers, read by the web app. | Phase 1, Phase 5 |

## Which Modeling Terms Does the Project Use?

| Term | What it means | Used in |
| :--- | :--- | :--- |
| Machine learning | Software that learns patterns from examples and then makes predictions on new cases. | All phases |
| Model | The learned pattern itself, stored as a set of numbers that turns features into a prediction. | Phase 2 |
| Supervised learning | Learning from examples that come with known answers. Every game has a known winner, so this project is supervised learning. | Phase 2 |
| Classification | Predicting which category something belongs to. | Phase 2 |
| Binary classification | Classification with two categories. Here: home win or away win. | Phase 2 |
| Regression (the task) | Predicting a number on a scale, such as a final score. This project does not do that. | Phase 2 |
| Prediction | The model's answer for one game: 1 for a home win or 0 for an away win. | Phase 2, Phase 3 |
| Probability | A number from 0 to 1 that says how likely the model thinks an outcome is. 0.64 means a 64% chance. | Phase 2, Phase 3 |
| Threshold | The cutoff that turns a probability into a pick. Here a home win probability above 0.5 picks the home team. | Phase 3 |
| Training | Letting the model study the training rows so it can find the pattern. Also called fitting. | Phase 2 |
| Training set | The games the model learns from. Here: 2016 to 2022. | Phase 1, Phase 2 |
| Validation set | Games used to compare model choices before the final score. Here: 2023. | Phase 1, Phase 2 |
| Test set | Games kept aside for the final score, to show how the model does on seasons it never saw. Here: 2024. | Phase 1, Phase 2 |
| Chronological split | Splitting data by date, so the model trains on the past and is scored on the future. | Phase 1 |
| Overfitting | When a model memorizes the training games instead of learning a pattern that carries to new games. Its training score is high and its test score is low. | Phase 2 |
| Baseline | A simple rule used for comparison. Here: always pick the home team. A model has to beat it to be useful. | Phase 1, Phase 2 |
| Scaler | A step that puts all features on a common scale so no feature dominates only because its numbers are larger. | Phase 2 |
| Standardization | The scaling this project uses: subtract the training average and divide by the training spread (standard deviation). | Phase 2 |
| Logistic regression | A simple classification model. It adds up the features with a weight for each and converts the sum to a probability between 0 and 1. Despite its name, it is used for classification. | Phase 2 |
| Weight (coefficient) | A number the model learns for each feature. A larger weight means that feature moves the prediction more. | Phase 2 |
| Intercept | A starting value the model adds before the features. In this project it captures the average home-field edge. | Phase 1, Phase 2 |
| Regularization | A penalty that keeps the weights small so the model does not overfit. | Phase 2 |
| `C` | The logistic regression setting for regularization strength. A smaller `C` means a stronger penalty. | Phase 2 |
| Solver | The method used to find the best weights. This project uses `lbfgs`. | Phase 2 |
| `max_iter` | The most steps the solver may take before it stops. | Phase 2 |
| Decision tree | A model that makes a prediction by answering a chain of yes or no questions about the features. | Phase 2 |
| Random forest | Many decision trees that each vote, with the majority winning. It is the second model type that can be compared. | Phase 2 |
| XGBoost | A popular library for boosted trees, which build trees one after another to fix earlier mistakes. The first design draft named it. This design leaves it out to keep the serving image small. | Phase 2 |
| Parameter | A value the model learns during training, such as a weight. | Phase 2 |
| Hyperparameter | A setting chosen before training, such as `C`. The settings file holds them. | Phase 2 |
| Random seed | A starting number for the computer's random choices. Using the same seed gives the same results on every run. | Phase 2 |
| Inference | Using a trained model to make a prediction for new input. The API does this. | Phase 3 |
| scikit-learn | The Python library that supplies the scaler and the models. | Phase 2, Phase 3 |
| Pipeline (scikit-learn) | One object that chains steps in order, here the scaler and then the model. Saving it as one object means the API cannot forget the scaling. | Phase 2, Phase 3 |
| joblib | A Python library for saving and loading trained models as files. | Phase 2, Phase 3 |
| SciPy | A Python library of scientific functions that scikit-learn depends on. | Phase 3 |
| Model version label | A name such as `v1.0` that identifies which trained model is running. | Phase 2, Phase 3 |

## Which Scoring Terms Does the Project Use?

| Term | What it means | Used in |
| :--- | :--- | :--- |
| Accuracy | The share of games where the predicted winner matches the real winner. This is the project's main metric. | Phase 2 |
| Baseline accuracy | The accuracy of always picking the home team: 54.85% on the training seasons, 55.51% in 2023, and 53.31% in 2024, after ties are removed. | Phase 1, Phase 2 |
| Confusion matrix | A small table that counts correct and wrong predictions for each real outcome: home wins predicted as home, home wins predicted as away, and so on. | Phase 2 |
| ROC curve | A chart showing how well the model separates home wins from away wins across every possible threshold. | Phase 2 |
| ROC-AUC | The area under the ROC curve, as a single number. 0.5 means no better than random ordering and 1.0 means perfect ordering. | Phase 2 |
| Log loss | A score that checks the probabilities, not just the picks. It punishes confident wrong answers heavily. Lower is better. | Phase 2 |
| Metric | Any number used to score a model. | Phase 2 |

## Which Experiment Tracking Terms Does the Project Use?

| Term | What it means | Used in |
| :--- | :--- | :--- |
| MLflow | A tool that records what happened in each training run so results can be compared and traced. | Phase 2 |
| Experiment | A named group of related runs in MLflow. | Phase 2 |
| Run | One execution of the training command, with its settings and results. | Phase 2 |
| Logging | Writing parameters, metrics, and files into the run record. | Phase 2 |
| Artifact | A file saved with a run, such as the saved model, a plot image, or a copy of the settings. | Phase 2 |
| Tracking location | Where MLflow stores run records. Here a local folder named `mlruns`, or a local database file. | Phase 2 |
| Weights & Biases | A hosted tool that does the same job as MLflow. The assignment allows either. This project uses MLflow. | Phase 2 |

## Which Configuration and Reproducibility Terms Does the Project Use?

| Term | What it means | Used in |
| :--- | :--- | :--- |
| Reproducibility | Getting the same result again from the same inputs, on any machine. | All phases |
| Python | The programming language of the data, training, and API code. | All phases |
| Virtual environment | A private folder of Python libraries for one project, so projects do not interfere. | Overview |
| `pip` | The tool that installs Python libraries. | Phase 1 |
| `requirements.txt` | A list of the Python libraries a project needs, with exact versions. | Phase 1 |
| Pinned version | An exact library version in a list, such as `scikit-learn 1.9.1`, so installs are identical. | Phase 1, Phase 3 |
| YAML | A readable text format for settings, written as indented `name: value` lines. | Phase 2 |
| `config.yaml` | The one file that holds every adjustable setting for the pipeline. | Phase 2 |
| Settings file | Any file that holds settings. Here, `config.yaml`. | Phase 2 |

## Which API Terms Does the Project Use?

| Term | What it means | Used in |
| :--- | :--- | :--- |
| API | A way for one program to ask another program for something over a network. Here the web app asks the prediction service for a prediction. | Phase 3 |
| Endpoint (route) | One address on an API that does one job, such as `/predict`. | Phase 3 |
| Request | The message a caller sends to the API. | Phase 3 |
| Response | The message the API sends back. | Phase 3 |
| `POST` and `GET` | Two kinds of request. `POST` sends data to be processed, like the three numbers. `GET` only asks for something, like the health check. | Phase 3 |
| Request body | The data sent along with a `POST` request. | Phase 3 |
| Input validation | Checking that incoming data has the right fields, types, and ranges before using it. | Phase 3 |
| Status code | A number that tells the caller how a request went. | Phase 3 |
| `200` | The request worked. | Phase 3 |
| `422` | The request was understood but the fields were wrong, such as a missing field or a value out of range. | Phase 3 |
| `429` | Too many requests. The throttle sends it. | Phase 4 |
| `500` | The service had an error. | Phase 3 |
| FastAPI | The Python framework that builds the API. | Phase 3 |
| Pydantic | The Python library FastAPI uses to check that requests have the right fields and types. | Phase 3 |
| Uvicorn | A server program that runs a FastAPI app on a local machine. | Phase 3 |
| ASGI | The standard way Python web apps and web servers talk to each other. | Phase 3 |
| Mangum | A small adapter that lets an ASGI app such as FastAPI run inside AWS Lambda. | Phase 3 |
| Handler | The function Lambda calls for each event. Here it passes the event to FastAPI. | Phase 3 |
| Health check | A route that reports whether the service is up and which model version it runs. | Phase 3, Phase 4 |
| `curl` | A command-line tool for sending requests, used to test the API. | Phase 3, Phase 4 |
| Postman | A desktop app for sending requests and reading responses, an alternative to `curl`. | Phase 3 |
| Cold start | The extra delay on the first request after Lambda has been idle, while it starts a new copy and loads the model. | Phase 3, Phase 4 |
| Stateless | Keeping nothing between requests. Each call stands alone. | Overview |
| Latency | The time between sending a request and getting the answer. | Phase 4 |
| CORS | A browser safety rule. A web page may call an API at another address only if the API says that page's address is allowed. | Phase 4, Phase 5 |
| Origin | The address a web page is served from: the protocol, the host name, and the port. | Phase 4 |
| Preflight request | A test request, using `OPTIONS`, that the browser sends first to ask whether the real request is allowed. | Phase 4, Phase 5 |

## Which Container Terms Does the Project Use?

| Term | What it means | Used in |
| :--- | :--- | :--- |
| Docker | A tool that packages a program with everything it needs, so it runs the same way on any machine. | Phase 3 |
| Image | The packaged, read-only snapshot of a program and its files. | Phase 3 |
| Container | A running copy of an image. | Phase 3 |
| Dockerfile | The text recipe that tells Docker how to build an image. | Phase 3 |
| Base image | The starting image that a new image builds on, such as a Python image. | Phase 3 |
| Build target | A named stage of a Dockerfile that can be built on its own. This project has `train` and `serve`. | Phase 3 |
| Multi-stage build | A Dockerfile with several stages, so one file can produce different images. | Phase 3 |
| Entry point | The command a container runs when it starts. | Phase 3 |
| `.dockerignore` | A list of files that Docker leaves out of the image. | Phase 3 |
| Lambda emulator | A small program in the AWS Lambda base image that lets the image be tested on a laptop. | Phase 3 |
| Processor architecture | The type of chip an image is built for, `arm64` or `x86_64`. An image and the Lambda function that runs it must match. | Phase 4 |
| Docker Desktop | The Docker application for a Mac or Windows computer. | Overview |

## Which AWS Terms Does the Project Use?

| Term | What it means | Used in |
| :--- | :--- | :--- |
| AWS | Amazon Web Services, a company's rented computing services. The project uses AWS for storage, hosting, and the API. | Phases 1, 4, 5 |
| Region | The geographic area where AWS resources run, such as `us-east-1`. | Phase 4 |
| Amazon S3 | A file storage service. | Phase 1, Phase 5 |
| Bucket | A named container for files in S3. Bucket names are unique across all of AWS. | Phase 1, Phase 5 |
| Object and key | An object is one file stored in S3. Its key is its path name inside the bucket. | Phase 1 |
| `boto3` | The Python library for calling AWS services from code. | Phase 1 |
| AWS credentials | The secret keys that prove who is calling AWS. They never go into the repository or an image. | Phase 1, Phase 4 |
| AWS CLI | AWS's command-line tool. | Phase 4 |
| IAM | Identity and Access Management, the AWS system for deciding who may do what. | Phase 4 |
| Policy | A list of actions an identity is allowed to take. | Phase 4 |
| Role | An identity that AWS services, such as Lambda, take on to get permissions. | Phase 4 |
| Least privilege | Giving each identity only the access its job needs. | Phase 4 |
| Amazon ECR | Elastic Container Registry, AWS's storage for Docker images. | Phase 4 |
| Image tag | A label on an image, here the model version. | Phase 4 |
| AWS Lambda | A service that runs code only when a request arrives, with no server to manage. | Phase 4 |
| API Gateway | The AWS service that gives Lambda a public web address and handles CORS and throttling. | Phase 4 |
| HTTP API | The simpler, lower-cost type of API Gateway that this project uses. | Phase 4 |
| Throttling | A limit on how many requests per second the API accepts. | Phase 4 |
| Amazon CloudWatch Logs | The AWS service that stores a function's log messages. | Phase 4 |
| AWS Budgets | A service that emails an alert when spending passes a limit. | Phase 4 |
| Free tier | The amount of an AWS service that costs nothing. Check AWS's current terms. | Phase 4 |
| Amazon CloudFront | A service that stores copies of files in many locations and serves them quickly over HTTPS. | Phase 5 |
| Origin access control | A CloudFront setting that lets only that distribution read a private bucket. | Phase 5 |
| Distribution | One CloudFront setup, with its own web address. | Phase 5 |
| Cache invalidation | A command that tells CloudFront to drop its stored copy of a file, so visitors get the new version. | Phase 5 |
| HTTPS | The secure version of the web protocol. It encrypts traffic between a browser and a site. | Phase 5 |

## Which Web App Terms Does the Project Use?

| Term | What it means | Used in |
| :--- | :--- | :--- |
| Front end | The part of a system a person sees and uses, here the web page. | Phase 5 |
| Single-page app | A web app that loads once and updates the page in the browser, without loading new pages. | Phase 5 |
| Vite | A tool for building web apps. It provides a local server for development and a build command for publishing. | Phase 5 |
| Development server | The local server started by `npm run dev`. It reloads the page on every file save. It is for development only. | Phase 5 |
| `vite build` | The command that turns the project into a folder of static files ready to publish. | Phase 5 |
| Static files | Files that are sent to the browser unchanged, such as HTML, CSS, and JavaScript. No server code runs. | Phase 5 |
| `dist` folder | The folder where `vite build` writes the files to publish. | Phase 5 |
| Content hash | A short code added to a built file's name. When the file changes, the name changes, so old cached copies are never reused. | Phase 5 |
| Node.js | The program that runs JavaScript tools, such as Vite, on a computer. | Phase 5 |
| `npm` | The tool that installs JavaScript libraries and runs project commands. | Phase 5 |
| `package.json` | The list of a JavaScript project's libraries and commands. | Phase 5 |
| Lock file | A file that records the exact library versions installed, so installs are identical. | Phase 5 |
| React | A JavaScript library for building user interfaces. It is the proposed template. | Phase 5 |
| TypeScript | JavaScript with type checks, which catch mistakes such as a misspelled field name before the app runs. | Phase 5 |
| `fetch` | The browser's built-in way to send a request to an API. | Phase 5 |
| Build-time setting | A value fixed when the files are built. `VITE_API_BASE_URL` is one, and it ends up readable inside the built files. | Phase 5 |
| Select box | A drop-down list for choosing one item. | Phase 5 |

## Which Project Process Terms Does the Project Use?

| Term | What it means | Used in |
| :--- | :--- | :--- |
| Phase | One of the five build steps. Each phase has its own guide. | Overview |
| Git | The tool that records the history of changes to a project. | Overview |
| Repository | The folder of project files together with its Git history. | Overview |
| GitHub | The website that hosts the repository. | Overview |
| Branch | A separate line of work in Git, so changes can be made without touching the main line. | Overview |
| Commit | A saved set of changes with a message. | Overview |
| Pull request | A request to merge a branch into the main line, where the changes can be reviewed first. | Overview |
| README | The front page of the repository. It explains the project and links to the live app and API. | Phase 5 |
| MkDocs | The tool that builds this documentation site from text files. | Overview |
| Mermaid | A way to write diagrams as text, used for the flow charts in these guides. | Overview |
| Acceptance check | A test with a clear pass condition, used to decide whether a step is finished. | All phases |
| Confirm note | A highlighted box marking a design choice that has a real alternative and needs the developer's approval. | All phases |
| Gap register | The list in the architecture overview of every earlier gap and where it is settled. | Overview |
