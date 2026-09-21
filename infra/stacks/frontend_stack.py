"""S3 + CloudFront frontend hosting, with /ask and /telemetry proxied to the API.

AWS Migration Plan, Section 3.2 ("Static hosting for a built SPA; pay per
GB served, scales infinitely, no servers") and Section 4, step 2: "the SPA
POSTs { text } to /api/ask, which CloudFront routes (via a separate cache
behavior) to the API origin instead of S3." This deployment keeps the
existing frontend's actual route names (`/ask`, `/telemetry` -
frontend/src/config/api.ts and backend/rag/main.py) rather than renaming
them to `/api/ask`, so no frontend or backend route code has to change for
the cutover - only two CloudFront cache behaviors.

Routing both through one CloudFront distribution also means the browser's
requests to /ask are same-origin in production, so ALLOWED_ORIGINS-based
CORS (backend_stack.py) only matters for local dev and any direct,
cross-origin calls to the API Gateway domain - not for normal production
traffic.

Deploy this after backend_stack.py (it takes the API's domain name as an
input) and build the frontend with VITE_API_BASE_URL="" so requests go to
same-origin relative paths (see docs/AWS_DEPLOYMENT.md).
"""

from __future__ import annotations

from aws_cdk import RemovalPolicy
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3_deployment
from constructs import Construct


class FrontendStack(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_name: str,
        api_domain_name: str,
        frontend_dist_dir: str | None = None,
        removal_policy: RemovalPolicy = RemovalPolicy.RETAIN,
    ) -> None:
        super().__init__(scope, construct_id)

        self.bucket = s3.Bucket(
            self,
            "FrontendBucket",
            bucket_name=None,  # let CFN generate a unique name
            removal_policy=removal_policy,
            auto_delete_objects=removal_policy == RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        s3_origin = origins.S3BucketOrigin.with_origin_access_control(self.bucket)
        api_origin = origins.HttpOrigin(
            api_domain_name,
            protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
        )

        # Caching disabled + all-viewer forwarding for the API behavior:
        # /ask is a POST with a JSON body and must not be cached, and needs
        # its headers/method forwarded through untouched.
        api_behavior = cloudfront.BehaviorOptions(
            origin=api_origin,
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
            allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
            origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        )

        self.distribution = cloudfront.Distribution(
            self,
            "Distribution",
            comment=f"{project_name} frontend + API edge",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=s3_origin,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            additional_behaviors={
                "/ask": api_behavior,
                "/telemetry": api_behavior,
            },
            error_responses=[
                # Client-side routed SPA: unknown paths fall back to index.html.
                cloudfront.ErrorResponse(
                    http_status=403, response_http_status=200, response_page_path="/index.html"
                ),
                cloudfront.ErrorResponse(
                    http_status=404, response_http_status=200, response_page_path="/index.html"
                ),
            ],
        )

        if frontend_dist_dir:
            s3_deployment.BucketDeployment(
                self,
                "DeployFrontend",
                sources=[s3_deployment.Source.asset(frontend_dist_dir)],
                destination_bucket=self.bucket,
                distribution=self.distribution,
                distribution_paths=["/*"],
            )

        self.domain_name = self.distribution.distribution_domain_name
