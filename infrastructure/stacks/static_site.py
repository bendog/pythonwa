# ruff: noqa: F841 - ignore unused variables
"""
Two constructs to host static sites in aws using S3, cloudfront and Route53.
StaticSitePrivateS3 creates a private S3 bucket and uses S3 API endpoint as
an origin in cloudfront and Origin Access Identity (OAI) to access the s3 objects.
StaticSitePublicS3 creates a public S3 bucket with website enabled and
uses Origin Custom Header (referer) to limit the access of s3 objects to the
CloudFront only.
"""

from pathlib import Path

from aws_cdk import (
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_certificatemanager as acm,
)
from aws_cdk import (
    aws_cloudfront as cloudfront,
)
from aws_cdk import (
    aws_cloudfront_origins as origins,
)
from aws_cdk import (
    aws_iam as iam,
)
from aws_cdk import (
    aws_route53 as route53,
)
from aws_cdk import (
    aws_route53_targets as targets,
)
from aws_cdk import (
    aws_s3 as s3,
)
from aws_cdk import (
    aws_s3_deployment as s3_deployment,
)
from aws_cdk import (
    aws_ssm as ssm,
)
from constructs import Construct

STACKS_PATH = Path(__file__).resolve().parent
PROJECT_ROOT = STACKS_PATH.parent.parent
FRONTEND_DIST_PATH = PROJECT_ROOT / "frontend" / "dist"


class StaticSite(Construct):
    """The base class for StaticSite constructs"""

    def __init__(
        self,
        scope,
        construct_id,
        site_domain_name,
        hosted_zone_id,
        hosted_zone_name,
        domain_certificate_arn=None,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        # Public variables
        self.bucket = None
        self.certificate = None
        self.distribution = None

        # Internal variables
        self._site_domain_name = site_domain_name

        # Instance Variables
        self.__domain_certificate_arn = domain_certificate_arn
        self.__hosted_zone_id = hosted_zone_id
        self.__hosted_zone_name = hosted_zone_name

    def _build_site(self):
        """The Template Method for building the site.
        It uses hook functions which are implemented in the sub classes
        """
        # Create the S3 bucket for the site contents
        self._create_site_bucket()

        # Get the hosted zone based on the provided domain name
        hosted_zone = self.__get_hosted_zone()

        # Get an existing or create a new certificate for the site domain
        self.__create_certificate(hosted_zone)

        # create the cloud front distribution
        self._create_cloudfront_distribution()

        # Create a Route53 record
        self.__create_route53_record(hosted_zone)

    def _create_site_bucket(self):
        """a virtual function to be implemented by the sub classes"""

    def _create_cloudfront_distribution(self):
        """a virtual function to be implemented by the sub classes"""

    def __get_hosted_zone(self):
        return route53.HostedZone.from_hosted_zone_attributes(
            self,
            "hosted_zone",
            zone_name=self.__hosted_zone_name,
            hosted_zone_id=self.__hosted_zone_id,
        )

    def __create_route53_record(self, hosted_zone):
        route53.ARecord(
            self,
            "site-alias-record",
            record_name=self._site_domain_name,
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(targets.CloudFrontTarget(self.distribution)),
        )

    def __create_certificate(self, hosted_zone):
        if self.__domain_certificate_arn:
            # If certificate arn is provided, import the certificate
            self.certificate = acm.Certificate.from_certificate_arn(
                self,
                "site_certificate",
                certificate_arn=self.__domain_certificate_arn,
            )
        else:
            # If certificate arn is not provided, create a new one.
            # ACM certificates that are used with CloudFront must be in
            # the us-east-1 region.
            self.certificate = acm.DnsValidatedCertificate(
                self,
                "site_certificate",
                domain_name=self._site_domain_name,
                hosted_zone=hosted_zone,
                region="us-east-1",
            )


class StaticSitePrivateS3(StaticSite):
    def __init__(
        self,
        scope,
        construct_id,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        self._build_site()

    def _create_site_bucket(self):
        """Creates a private S3 bucket for the static site construct"""
        self.bucket = s3.Bucket(
            self,
            "site_bucket",
            bucket_name=self._site_domain_name,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

    def _create_cloudfront_distribution(self):
        """Create a cloudfront distribution with a private bucket as the origin"""
        self.distribution = cloudfront.Distribution(
            self,
            "cloudfront_distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(self.bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            domain_names=[self._site_domain_name],
            certificate=self.certificate,
            default_root_object="index.html",
        )


class StaticSitePublicS3(StaticSite):
    def __init__(
        self,
        scope,
        construct_id,
        origin_referer_header_parameter_name,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        # Get the origin referer header value
        self.__origin_referer_header = self.__get_referer_header(
            origin_referer_header_parameter_name,
        )

        self._build_site()

    def __get_referer_header(self, parameter_name):
        return ssm.StringParameter.from_string_parameter_attributes(
            self, "custom_header", parameter_name=parameter_name
        ).string_value

    def _create_site_bucket(self):
        """Creates a public S3 bucket for the static site construct"""
        self.bucket = s3.Bucket(
            self,
            "site_bucket",
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
            public_read_access=True,
            # object_ownership=s3.ObjectOwnership.OBJECT_WRITER,
            bucket_name=self._site_domain_name,
            website_index_document="index.html",
            website_error_document="404.html",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        bucket_policy = iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[self.bucket.arn_for_objects("*")],
            principals=[iam.AnyPrincipal()],
        )
        bucket_policy.add_condition(
            "StringEquals",
            {"aws:Referer": self.__origin_referer_header},
        )

        self.bucket.add_to_resource_policy(bucket_policy)

    def _create_cloudfront_distribution(self):
        """Create a cloudfront distribution with a public bucket as the origin"""
        origin_source = cloudfront.CustomOriginConfig(
            domain_name=self.bucket.bucket_website_domain_name,
            origin_protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
            origin_headers={"Referer": self.__origin_referer_header},
        )

        # TODO: need to update this to use the new distribution method.
        #   https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudfront/Distribution.html

        self.distribution = cloudfront.CloudFrontWebDistribution(
            self,
            "cloudfront_distribution",
            viewer_certificate=cloudfront.ViewerCertificate.from_acm_certificate(
                self.certificate,
                aliases=[self._site_domain_name],
                security_policy=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2019,
                ssl_method=cloudfront.SSLMethod.SNI,
            ),
            origin_configs=[
                cloudfront.SourceConfiguration(
                    custom_origin_source=origin_source,
                    behaviors=[
                        cloudfront.Behavior(
                            is_default_behavior=True,
                        )
                    ],
                )
            ],
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            price_class=cloudfront.PriceClass.PRICE_CLASS_ALL,
        )


class RedirectSitePublicS3(StaticSitePublicS3):
    def _create_site_bucket(self):
        """Creates a public S3 bucket for the static site construct"""
        self.bucket = s3.Bucket(
            self,
            "redirect_site_bucket",
            bucket_name=self._site_domain_name,
            # website_index_document="index.html",
            # website_error_document="404.html",
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
            public_read_access=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            # TODO: this is very ugly, shouldn't be here, testing it out.
            website_redirect=s3.RedirectTarget(
                host_name="www." + self._site_domain_name, protocol=s3.RedirectProtocol.HTTPS
            ),
        )
        bucket_policy = iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[self.bucket.arn_for_objects("*")],
            principals=[iam.AnyPrincipal()],
        )
        # bucket_policy.add_condition(
        #     "StringEquals",
        #     {"aws:Referer": self.__origin_referer_header},
        # )

        self.bucket.add_to_resource_policy(bucket_policy)


class StaticWebStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        site_domain_name: str,
        domain_certificate_arn: str,
        hosted_zone_id: str,
        hosted_zone_name: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        site = StaticSitePublicS3(
            self,
            f"{construct_id}-StaticSitePublicS3",
            site_domain_name="www." + site_domain_name,
            domain_certificate_arn=domain_certificate_arn,
            origin_referer_header_parameter_name="/prod/static-site/origin-custom-header/referer",
            hosted_zone_id=hosted_zone_id,
            hosted_zone_name=hosted_zone_name,
        )

        # noinspection PyUnusedLocal
        redirect = RedirectSitePublicS3(
            self,
            f"{construct_id}-RedirectSitePublicS3",
            site_domain_name=site_domain_name,
            domain_certificate_arn=domain_certificate_arn,
            origin_referer_header_parameter_name="/prod/static-site/origin-custom-header/referer",
            hosted_zone_id=hosted_zone_id,
            hosted_zone_name=hosted_zone_name,
        )

        # noinspection PyUnusedLocal
        files = s3_deployment.BucketDeployment(
            self,
            f"{construct_id}-BucketDeployment",
            sources=[s3_deployment.Source.asset(str(FRONTEND_DIST_PATH))],
            destination_bucket=site.bucket,
            prune=True,
        )
