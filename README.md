# Amazon Q - GitLab Integration

This project demonstrates an integration of Amazon Q, AWS services, and GitLab for managing Git commands and automating repository tasks. The application uses Streamlit for the front-end interface and AWS services like Cognito, IAM, and STS for authentication and authorization.

You can view a short demo video in the "Demo" folder.

## Features

- **GitLab Integration**: Execute Git and `glab` commands directly through a web interface.
- **Authentication**: Authenticate users via AWS Cognito.
- **AWS Service Integration**: Leverage Amazon Q and IAM roles for secure interactions.
- **Dynamic Git Commands**: Generate and execute Git commands dynamically based on user input.
- **Streamlit Interface**: Simple and interactive web-based UI.

## Requirements

### Prerequisites

- Python 3.8 or later
- AWS credentials with appropriate permissions
- GitLab CLI (`glab`) installed in `/opt/homebrew/bin`
- Dependencies listed in `requirements.txt`

### Python Libraries

Install the required libraries:
```bash
pip install boto3 streamlit jwt
```

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Update Configuration**:
   - Replace placeholders in the code (`XXXXXX`, `cognito_client_id`, `arn:aws:iam`, etc.) with your actual values.

3. **Run the Application**:
   ```bash
   streamlit run app.py
   ```

4. **Access the App**:
   Open the URL displayed in the terminal, typically `http://localhost:8501`.

## How It Works

1. **User Input**:
   Users input Git-related questions into the Streamlit app.

2. **AWS Cognito Authentication**:
   Authenticate the user using AWS Cognito credentials.

3. **Token Creation with IAM**:
   Generate IAM tokens using the JWT token.

4. **Role Assumption**:
   Assume a specified AWS IAM role to obtain temporary credentials.

5. **Amazon Q Interaction**:
   Use Amazon Q to generate appropriate Git commands.

6. **Command Execution**:
   Execute the generated commands in the local Git repository and display the results.

7. **Follow-Up**:
   Provide a detailed summary of the executed commands and outcomes.

## Example Usage

1. Enter a question like:
   ```
   How do I create a new feature branch and push it to GitLab?
   ```

2. The app will generate and display the Git commands, such as:
   ```bash
   git checkout -b feature1
   git add .
   git commit -m "Initial commit"
   git push origin feature1
   ```

3. The commands will be executed, and the app will display the results and summary.

## Error Handling

- If any AWS service call fails, the app will display an error message and stop execution.
- Ensure all required permissions and configurations are correctly set.