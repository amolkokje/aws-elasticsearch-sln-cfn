# aws-elasticsearch-sln-cfn
Cloudformation templates and code to deploy secure AWS Elasticsearch solution


## Deploy Stack:
1. Create and upload Lambda packages using create_lambda_package.sh
2. Deploy CFN, with ARN of Cognito identity auth role
3. Go to AWS Console, and configure Cognito auth

## Update Lambda functions:
1. Change the code as needed.
2. Go to the 'functions' folder and run command "sam build --template lambda_template.yaml".
   This will create dir .aws-sam if it does not exist and add the packages there.
3. Run the command "sam package --s3-bucket elasticsearch-lambda-functions".
   This will package the lambda function code along with its dependencies and upload the package to the staging bucket.
4. Since the previous step generates a random name, update the names of the deployed function pacakges using CLI.
   Example: aws s3 mv s3://elasticsearch-lambda-functions/<NAME> s3://elasticsearch-lambda-functions/index_data_<NAME>
5. Now, update the name of the lambda function Mapping in the Cloudformation template:
   Mappings:
     LambdaFunctionPackage:
        IndexDataFunction:
         Package: index_data_9a2b8349d1fd859e394dc43ae8d5d040

