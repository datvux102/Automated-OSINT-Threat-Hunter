param(
    [Parameter(Mandatory = $true)]
    [string]$StackName,

    [Parameter(Mandatory = $true)]
    [string]$S3Bucket,

    [string]$Region = "us-east-1",
    [string]$AlertThreshold = "CRITICAL",
    [string]$SystemPromptPath = "prompts/system_prompt.txt",
    [string]$BedrockModelId = "",
    [string]$SnsTopicArn = "",
    [string]$GitHubTokenSecretArn = "",
    [string]$AlarmNotificationTopicArn = "",
    [string]$DefaultSource = "github",
    [string]$DefaultQuery = "",
    [string]$GitHubApiUrl = "https://api.github.com",
    [string]$GitHubApiVersion = "2022-11-28",
    [int]$GitHubMaxAttempts = 3,
    [double]$GitHubBackoffSeconds = 1.0,
    [int]$GitHubPerPage = 5,
    [int]$GitHubMaxPages = 1
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command sam -ErrorAction SilentlyContinue)) {
    throw "AWS SAM CLI is required. Install it before running this script."
}

$parameterOverrides = @(
    "AlertThreshold=$AlertThreshold"
    "SystemPromptPath=$SystemPromptPath"
    "BedrockModelId=$BedrockModelId"
    "SnsTopicArn=$SnsTopicArn"
    "GitHubTokenSecretArn=$GitHubTokenSecretArn"
    "AlarmNotificationTopicArn=$AlarmNotificationTopicArn"
    "DefaultSource=$DefaultSource"
    "DefaultQuery=$DefaultQuery"
    "GitHubApiUrl=$GitHubApiUrl"
    "GitHubApiVersion=$GitHubApiVersion"
    "GitHubMaxAttempts=$GitHubMaxAttempts"
    "GitHubBackoffSeconds=$GitHubBackoffSeconds"
    "GitHubPerPage=$GitHubPerPage"
    "GitHubMaxPages=$GitHubMaxPages"
)

sam build --template-file template.yaml

sam deploy `
    --stack-name $StackName `
    --s3-bucket $S3Bucket `
    --region $Region `
    --capabilities CAPABILITY_IAM `
    --no-confirm-changeset `
    --parameter-overrides $parameterOverrides
