from mentaws import aws_operations


def test_region_setting():

    assert aws_operations.get_region("default") == "ap-southeast-1"
    assert aws_operations.get_region("mentaws1") == "ap-southeast-1"
    assert aws_operations.get_region("mentaws2") == "ap-southeast-2"
    assert aws_operations.get_region("mentaws3") == "ap-southeast-1"
