#!/usr/bin/env python3
"""
Setup API Gateway in LocalStack with routes to Lambda handlers
"""
import boto3
import json
import sys

# Configure boto3 for LocalStack
client = boto3.client(
    'apigateway',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

lambda_client = boto3.client(
    'lambda',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

print("\n" + "=" * 70)
print("🚀 Setting up API Gateway in LocalStack")
print("=" * 70)

try:
    # 1. Create REST API
    print("\n1. Creating REST API...")
    api = client.create_rest_api(
        name='instagram-service',
        description='Instagram Image Service API',
        endpointConfiguration={'types': ['REGIONAL']}
    )
    api_id = api['id']
    print(f"   ✅ API created: {api_id}")

    # 2. Get the root resource
    print("\n2. Getting root resource...")
    resources = client.get_resources(restApiId=api_id)
    root_id = resources['items'][0]['id']
    print(f"   ✅ Root resource: {root_id}")

    # 3. Create /images resource
    print("\n3. Creating /images resource...")
    images_resource = client.create_resource(
        restApiId=api_id,
        parentId=root_id,
        pathPart='images'
    )
    images_id = images_resource['id']
    print(f"   ✅ /images resource created: {images_id}")

    # 4. Create /images/{image_id} resource
    print("\n4. Creating /images/{{image_id}} resource...")
    image_id_resource = client.create_resource(
        restApiId=api_id,
        parentId=images_id,
        pathPart='{image_id}'
    )
    image_id_id = image_id_resource['id']
    print(f"   ✅ /images/{{image_id}} resource created: {image_id_id}")

    # 5. Create /images/upload resource
    print("\n5. Creating /images/upload resource...")
    upload_resource = client.create_resource(
        restApiId=api_id,
        parentId=images_id,
        pathPart='upload'
    )
    upload_id = upload_resource['id']
    print(f"   ✅ /images/upload resource created: {upload_id}")

    # 6. Create POST /images/upload method
    print("\n6. Creating POST /images/upload method...")
    client.put_method(
        restApiId=api_id,
        resourceId=upload_id,
        httpMethod='POST',
        authorizationType='NONE'
    )
    print("   ✅ POST method created")

    # 7. Create integration with upload Lambda
    print("\n7. Creating integration with upload Lambda...")
    client.put_integration(
        restApiId=api_id,
        resourceId=upload_id,
        httpMethod='POST',
        type='AWS_PROXY',
        integrationHttpMethod='POST',
        uri=f'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:upload-image/invocations'
    )
    print("   ✅ Integration created")

    # 8. Create 200 response
    print("\n8. Creating response method...")
    client.put_method_response(
        restApiId=api_id,
        resourceId=upload_id,
        httpMethod='POST',
        statusCode='200'
    )
    client.put_integration_response(
        restApiId=api_id,
        resourceId=upload_id,
        httpMethod='POST',
        statusCode='200',
        responseTemplates={'application/json': ''}
    )
    print("   ✅ Response created")

    # 9. Create GET /images method
    print("\n9. Creating GET /images method...")
    client.put_method(
        restApiId=api_id,
        resourceId=images_id,
        httpMethod='GET',
        authorizationType='NONE'
    )
    client.put_integration(
        restApiId=api_id,
        resourceId=images_id,
        httpMethod='GET',
        type='AWS_PROXY',
        integrationHttpMethod='POST',
        uri=f'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:list-images/invocations'
    )
    client.put_method_response(
        restApiId=api_id,
        resourceId=images_id,
        httpMethod='GET',
        statusCode='200'
    )
    client.put_integration_response(
        restApiId=api_id,
        resourceId=images_id,
        httpMethod='GET',
        statusCode='200',
        responseTemplates={'application/json': ''}
    )
    print("   ✅ GET /images method created")

    # 10. Create GET /images/{image_id} method
    print("\n10. Creating GET /images/{{image_id}} method...")
    client.put_method(
        restApiId=api_id,
        resourceId=image_id_id,
        httpMethod='GET',
        authorizationType='NONE'
    )
    client.put_integration(
        restApiId=api_id,
        resourceId=image_id_id,
        httpMethod='GET',
        type='AWS_PROXY',
        integrationHttpMethod='POST',
        uri=f'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:get-image/invocations'
    )
    client.put_method_response(
        restApiId=api_id,
        resourceId=image_id_id,
        httpMethod='GET',
        statusCode='200'
    )
    client.put_integration_response(
        restApiId=api_id,
        resourceId=image_id_id,
        httpMethod='GET',
        statusCode='200',
        responseTemplates={'application/json': ''}
    )
    print("   ✅ GET /images/{{image_id}} method created")

    # 11. Create DELETE /images/{image_id} method
    print("\n11. Creating DELETE /images/{{image_id}} method...")
    client.put_method(
        restApiId=api_id,
        resourceId=image_id_id,
        httpMethod='DELETE',
        authorizationType='NONE'
    )
    client.put_integration(
        restApiId=api_id,
        resourceId=image_id_id,
        httpMethod='DELETE',
        type='AWS_PROXY',
        integrationHttpMethod='POST',
        uri=f'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:delete-image/invocations'
    )
    client.put_method_response(
        restApiId=api_id,
        resourceId=image_id_id,
        httpMethod='DELETE',
        statusCode='200'
    )
    client.put_integration_response(
        restApiId=api_id,
        resourceId=image_id_id,
        httpMethod='DELETE',
        statusCode='200',
        responseTemplates={'application/json': ''}
    )
    print("   ✅ DELETE /images/{{image_id}} method created")

    # 12. Deploy API
    print("\n12. Deploying API...")
    deployment = client.create_deployment(
        restApiId=api_id,
        stageName='dev'
    )
    print(f"   ✅ API deployed")

    # 13. Print endpoint
    print("\n" + "=" * 70)
    print("✅ API Gateway Setup Complete!")
    print("=" * 70)
    print(f"\nAPI ID: {api_id}")
    print(f"\nEndpoints:")
    print(f"  POST   http://localhost:4566/restapis/{api_id}/stages/dev/_user_request_/images/upload")
    print(f"  GET    http://localhost:4566/restapis/{api_id}/stages/dev/_user_request_/images")
    print(f"  GET    http://localhost:4566/restapis/{api_id}/stages/dev/_user_request_/images/{{image_id}}")
    print(f"  DELETE http://localhost:4566/restapis/{api_id}/stages/dev/_user_request_/images/{{image_id}}")

    print(f"\nOr using the simpler LocalStack endpoint format:")
    print(f"  http://localhost:4566/images/upload (POST)")
    print(f"  http://localhost:4566/images (GET)")
    print(f"  http://localhost:4566/images/{{image_id}} (GET/DELETE)")

    print("\n" + "=" * 70 + "\n")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
