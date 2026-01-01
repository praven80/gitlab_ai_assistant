import streamlit as st
import boto3
import jwt
import re
import subprocess
from botocore.exceptions import ClientError
import os

# Manually set the PATH to include the directory where glab is installed
os.environ["PATH"] += os.pathsep + "/opt/homebrew/bin/glab"

# Streamlit page configuration
st.set_page_config(page_title="Amazon Q - GitLab Integration", page_icon=":rocket:", layout='wide')
st.image('https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg', width=200)

# Display header
st.header("Amazon Q - GitLab Integration")
st.write("-----")

# Path to the local Git repository
repo_path = "/Users/Documents/Projects/gitlab_project/project1"

# Function to authenticate the user using Cognito
def authenticate_user():
    client = boto3.client('cognito-idp')
    try:
        response = client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': 'user_id',
                'PASSWORD': 'Password1!'
            },
            ClientId='cognito_client_id' #Replace your Cognito Client Id
        )
        return response['AuthenticationResult']['IdToken']
    except ClientError as e:
        st.error(f"Authentication failed: {e}")
        st.stop()

# Function to create a token with IAM using the JWT token
def create_token_with_iam(jwt_token):
    client = boto3.client("sso-oidc")
    try:
        response = client.create_token_with_iam(
            clientId='arn:aws:sso::XXXXX:application/ssoins/apl-client-id', #Replace your Client Id
            grantType="urn:ietf:params:oauth:grant-type:jwt-bearer",
            assertion=jwt_token
        )
        return response
    except ClientError as e:
        st.error(f"Token creation with IAM failed: {e}")
        st.stop()

# Function to assume a role and get AWS credentials
def assume_role(decoded_token):
    sts_client = boto3.client("sts")
    try:
        response = sts_client.assume_role(
            RoleArn='arn:aws:iam::XXXXXX:role/Admin', #Replace your IAM Role ARN
            RoleSessionName="qapp",
            ProvidedContexts=[
                {
                    "ProviderArn": "arn:aws:iam::aws:contextProvider/IdentityCenter",
                    "ContextAssertion": decoded_token["sts:identity_context"],
                }
            ],
        )
        return response["Credentials"]
    except ClientError as e:
        st.error(f"Role assumption failed: {e}")
        st.stop()

# Function to get the Amazon Q client using the assumed AWS credentials
def get_amazon_q_client(aws_credentials):
    session = boto3.Session(
        aws_access_key_id=aws_credentials["AccessKeyId"],
        aws_secret_access_key=aws_credentials["SecretAccessKey"],
        aws_session_token=aws_credentials["SessionToken"],
    )
    return session.client("qbusiness")

# Function to clean CDATA tags from text
def clean_cdata(text):
    return re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text).strip()

# Function to execute a Git command
def execute_git_command(command):
    try:
        result = subprocess.run(
            command,
            cwd=repo_path,
            shell=True,
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"An error occurred while executing the command: {e}"

# Streamlit app logic
user_message = st.text_input("Enter your Git-related question:")
if st.button("Submit"):
    with st.spinner('Authenticating...'):
        jwt_token = authenticate_user()

    with st.spinner('Creating token with IAM...'):
        iam_response = create_token_with_iam(jwt_token)
        decoded_token = jwt.decode(iam_response["idToken"], options={"verify_signature": False})

    with st.spinner('Assuming role...'):
        aws_credentials = assume_role(decoded_token)

    with st.spinner('Getting Amazon Q client...'):
        amazon_q = get_amazon_q_client(aws_credentials)

    with st.spinner('Calling Amazon Q...'):
        ai_prompt = (
            "You are a GitLab expert. Based on the following question, "
            f"frame the appropriate Git or glab commands by interacting with the local repository checked-out at {repo_path}.\n\n"
            f"Question: {user_message}\n\n"
            "Show the complete set of Git or glab commands in XML tags that can be executed in the terminal to achieve the desired outcome.\n\n"
            "The commands should:\n"
            "1. Generate or update the code according to the user's specifications.\n"
            "2. Create a new feature branch in GitLab with a meaningful name (e.g., \n<command>git checkout -b feature1)</command>).\n"
            "3. Add the newly created or modified code to this feature branch (e.g., \n<command>git add first.py)</command>).\n"
            "4. Commit the changes with a descriptive commit message (e.g., \n<command>git commit -m 'Add first.py file')</command>).\n"
            "5. Push the feature branch to the remote repository (e.g., \n<command>git push origin feature1)</command>).\n\n"
            "DO NOT give me the command for just one step, Wait for all the steps to be completed and "
            "concatenate all the generated commands into a single response, ensuring they are in the correct order for execution.\n"
            " Include the commands for code generation, branch creation of the feature branch and the commit process "
            "and pushing the feature branch to the remote repository.\n\n"
            "When the user is requesting to merege the changes, generate gitlab command to merge"
            "Example: \n<command>git checkout main \n git pull origin main \n git merge feature1 \n git push origin main </command>\n\n"
            "If the question is not related to Git or glab, simply respond with 'I am not sure how to handle that.'"
        )

        try:
            answer = amazon_q.chat_sync(
                applicationId='XXXXXX',  # Amazon Q Application ID
                userMessage=ai_prompt
            )
            response_text = answer["systemMessage"]
        except ClientError as e:
            st.error(f"Chat sync API call failed: {e}")
            st.stop()

        # Clean and extract the Git command from the response
        git_command = clean_cdata(re.search(r'<command>\s*(.*?)\s*</command>', response_text, re.DOTALL).group(1))
        st.code(git_command, language='bash')

        # Execute the Git command and display the response
        git_response = execute_git_command(git_command)
        git_response = git_response[:6740] #Input token cannot exceed 7000 characters, so limiting the output to 6740 characters

        # Prepare a follow-up prompt for summarizing the outcome
        follow_up_prompt = (
            "The Git command was executed successfully. "
            "Provide a detailed summary of the outcome in less than 1000 words."
            f"\n\nQuestion: {user_message}\n\n"
            f"Git Command: {git_command}\n\n"
            f"Git Response: {git_response}\n\n"
            "Summary:"
        )
        try:
            answer = amazon_q.chat_sync(
                applicationId='XXXXXX',  # Amazon Q Application ID
                userMessage=follow_up_prompt
            )
            st.write(answer["systemMessage"])
        except ClientError as e:
            st.error(f"Follow-up API call failed: Git command was not successful !")
            st.error(f"Follow-up API call failed: {e}")