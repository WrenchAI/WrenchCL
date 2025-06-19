# import pytest
# from uuid import UUID
#
# from pydantic import ValidationError, BaseModel
#
# from Types.CompositeTypeValidatorMixin import TypeCoercionMixin
# from Types.CompositeTypes import (
#     UUIDLike, IntLike, FloatLike, BoolLike,
#     JSONLike, OptionalJSON, StrOrList, IntOrList,
#     PathLike, ARN, S3Url, S3Uri, LinkedInProfileUrl,
#     LinkedInCompanyUrl, HttpUrl, Uri, AWSResourceURI
# )
#
#
# # ─────────────────────────────────────────────────────────────
# # Models for Testing
# # ─────────────────────────────────────────────────────────────
# class TestModel(TypeCoercionMixin, BaseModel):
#     uuid: UUIDLike
#     integer: IntLike
#     floating: FloatLike
#     active: BoolLike
#     jsondata: JSONLike
#     optional_json: OptionalJSON
#     tags: StrOrList
#     counts: IntOrList
#     path: PathLike
#     arn: ARN
#     s3url: S3Url
#     s3uri: S3Uri
#     profile: LinkedInProfileUrl
#     company: LinkedInCompanyUrl
#     homepage: HttpUrl
#     resource: AWSResourceURI
#     endpoint: Uri
#
#     class Config:
#         UUIDLike_rtype = str
#         IntLike_rtype = int
#         FloatLike_rtype = str
#         BoolLike_rtype = str
#         JSONLike_rtype = str
#         StrOrList_rtype = str
#         IntOrList_rtype = list
#         PathLike_rtype = str
#         HttpUrl_rtype = str
#
#
# # ─────────────────────────────────────────────────────────────
# # Valid Input Test
# # ─────────────────────────────────────────────────────────────
#
# def test_valid_inputs():
#     m = TestModel(
#         uuid="5d30b637-ad35-4a53-bc51-59f613b63be6",
#         integer="42",
#         floating="3.14159",
#         active="yes",
#         jsondata='{"key":"value"}',
#         optional_json=None,
#         tags="dev",
#         counts=[1, 2],
#         path="some/file.txt",
#         arn="arn:aws:s3:::bucket/key",
#         s3url="https://s3.us-east-1.amazonaws.com/bucket/key",
#         s3uri="s3://bucket/key",
#         profile="https://www.linkedin.com/in/example/",
#         company="https://www.linkedin.com/company/test/",
#         homepage="https://example.com",
#         resource="arn:aws:lambda:us-east-1:123456789012:function:my-func",
#         endpoint="https://api.example.com"
#     )
#
#     assert isinstance(m.uuid, str)
#     assert m.uuid == "5d30b637-ad35-4a53-bc51-59f613b63be6"
#     assert isinstance(m.integer, int)
#     assert isinstance(m.floating, str)
#     assert m.floating.startswith("3.")
#     assert m.active == "true"
#     assert m.optional_json is None
#     assert m.jsondata == '{"key": "value"}'
#     assert m.tags == "dev"
#     assert m.counts == [1, 2]
#     assert m.path == "some/file.txt"
#     assert m.arn.startswith("arn:")
#     assert m.s3url.startswith("https://s3")
#     assert m.s3uri.startswith("s3://")
#     assert m.profile.startswith("https://")
#     assert m.company.startswith("https://")
#     assert m.homepage.startswith("https://")
#     assert m.resource.startswith("arn:")
#     assert m.endpoint.startswith("https://")
#
#
# # ─────────────────────────────────────────────────────────────
# # Error Cases
# # ─────────────────────────────────────────────────────────────
#
# def test_invalid_uuid():
#     with pytest.raises(ValidationError):
#         TestModel(uuid="not-a-uuid", integer="1", floating="1.0", active=True,
#                   jsondata={}, optional_json=None, tags=[], counts=[], path="x",
#                   arn="arn:x", s3url="https://s3.us-east-1.amazonaws.com/x", s3uri="s3://x",
#                   profile="https://www.linkedin.com/in/test/", company="https://linkedin.com/company/test",
#                   homepage="https://x.com", resource="arn:x", endpoint="https://x")
#
# def test_invalid_boollike():
#     with pytest.raises(ValidationError):
#         TestModel(uuid="5d30b637-ad35-4a53-bc51-59f613b63be6", integer=1, floating=1.1, active="maybe",
#                   jsondata={}, optional_json=None, tags=[], counts=[], path="x",
#                   arn="arn:x", s3url="https://s3.us-east-1.amazonaws.com/x", s3uri="s3://x",
#                   profile="https://www.linkedin.com/in/test/", company="https://linkedin.com/company/test",
#                   homepage="https://x.com", resource="arn:x", endpoint="https://x")
#
#
# def test_invalid_linkedin_company_url():
#     with pytest.raises(ValidationError):
#         TestModel(uuid="5d30b637-ad35-4a53-bc51-59f613b63be6", integer=1, floating=1.1, active=True,
#                   jsondata={}, optional_json=None, tags=[], counts=[], path="x",
#                   arn="arn:x", s3url="https://s3.us-east-1.amazonaws.com/x", s3uri="s3://x",
#                   profile="https://www.linkedin.com/in/test/",
#                   company="https://example.com/company/test",
#                   homepage="https://x.com", resource="arn:x", endpoint="https://x")
#
#
# # ─────────────────────────────────────────────────────────────
# # Output Serialization Behavior
# # ─────────────────────────────────────────────────────────────
#
# def test_model_dump_uses_internal_types():
#     m = TestModel(
#         uuid="5d30b637-ad35-4a53-bc51-59f613b63be6",
#         integer="42",
#         floating="3.14",
#         active=True,
#         jsondata={"x": 1},
#         optional_json=None,
#         tags=["foo"],
#         counts=[7, 8],
#         path="my/file",
#         arn="arn:aws:s3:::bucket/key",
#         s3url="https://s3.us-east-1.amazonaws.com/bucket/key",
#         s3uri="s3://bucket/key",
#         profile="https://www.linkedin.com/in/test/",
#         company="https://www.linkedin.com/company/org/",
#         homepage="https://test.com",
#         resource="arn:aws:lambda:us-east-1:123456789012:function:func",
#         endpoint="https://api.example.com"
#     )
#
#     d = m.model_dump()
#     assert isinstance(d["uuid"], UUID)  # Stored internally as UUID
#     assert isinstance(d["integer"], int)
#     assert isinstance(d["floating"], float)
#     assert d["jsondata"] == {"x": 1}
#     assert d["optional_json"] is None
#     assert d["tags"] == ["foo"]
#     assert d["counts"] == [7, 8]
