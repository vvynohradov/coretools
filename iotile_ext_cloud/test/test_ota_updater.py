import pytest
from builtins import range
from iotile.core.dev.semver import SemanticVersion
from iotile.cloud.apps import OtaUpdater


def test_ota_app_creation(ota_cloud, simple_hw):

    cloud, _proj_id, _server = ota_cloud

    hw = simple_hw
    app_tag = 123
    app_version = SemanticVersion(0,0,1)
    os_tag = 234
    os_version = SemanticVersion(0,0,1)
    app_info = [app_tag, app_version]
    os_info = [os_tag, os_version]

    device_id = 1
    hw.connect(device_id)
    ota_updater = OtaUpdater(hw, app_info, os_info, device_id)
    assert ota_updater is not None


def test_no_deployments(ota_cloud, simple_hw):
    cloud, _proj_id, _server = ota_cloud
    hw = simple_hw
    hw.connect(3)

    ota_updater = OtaUpdater(hw, [123, SemanticVersion(0,0,1)], [234, SemanticVersion(0,0,1)], 3)

    actual_result = ota_updater.check_cloud_for_script()

    assert not actual_result


def test_apply_update(ota_cloud, simple_hw):

    cloud, _proj_id, _server = ota_cloud

    hw = simple_hw
    app_tag = 123
    app_version = SemanticVersion(0,0,2)
    os_tag = 234
    os_version = SemanticVersion(0,0,2)
    app_info = [app_tag, app_version]
    os_info = [os_tag, os_version]

    device_id = 1
    hw.connect(device_id)
    ota_updater = OtaUpdater(hw, app_info, os_info, device_id)

    blob = b'\x8e\x9a\x1fG\x8e)\x92\xc1\xbaz\x9e\xd3\x9a@\x86\x10L=.\x1f\x1a\x05\x00\x00\x0e\x00\x00\x00\x04\x00\x00\x00\x05 \x08\x08\x00\x00\x0c\x00\x00\x00\x04\x00\x00\x00\x0c \x08\x08\x0c\x00\x00\x00\x04\x00\x00\x00\r \x08\x08 \x00\x00\x00\x04\x00\x00\x00\x03 \x08\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00D\x028\xff\xff\x00\n\n\x01\x00\x00 \x00\x00\x00\x04\x00\x00\x00\x03 \x08\x08\x00\x00\x00\x00\x00\x00\x00\x00\x01D\x038\xff\xff\x00\n\n\x01\x00\x00 \x00\x00\x00\x04\x00\x00\x00\x03 \x08\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x14\x01<\xff\xff\x00\n\n\x01\x00\x00 \x00\x00\x00\x04\x00\x00\x00\x03 \x08\x08\x00\x00\x00\x00\x00\x00\x00\x00\x01\x14\x02<\xff\xff\x00\n\n\x01\x00\x00 \x00\x00\x00\x04\x00\x00\x00\x03 \x08\x08\x00\x00\x00\x00\x00\x00\x00\x00\x04\x14\x008\xff\xff\x00\n\n\x01\x00\x00 \x00\x00\x00\x04\x00\x00\x00\x03 \x08\x08\x00\x00\x00\x00\x08\x00\x00\x00\x01$\x02$\x00\x14\x00\n\x08\x00\x00\x00 \x00\x00\x00\x04\x00\x00\x00\x03 \x08\x08\x00\x00\x00\x00\x08\x00\x00\x00\x01$\x03$\x01\x14\x00\n\x08\x00\x00\x00 \x00\x00\x00\x04\x00\x00\x00\x03 \x08\x08\x01\x00\x00\x00\x00\x00\x00\x00\x01P\x00D\x00$\x06\x05\n\x00\x00\x00 \x00\x00\x00\x04\x00\x00\x00\x03 \x08\x08\x01\x00\x00\x00\x00\x00\x00\x00\x03\x14\x00\x14\x05$\x05\t\n\x00\x00\x00 \x00\x00\x00\x04\x00\x00\x00\x03 \x08\x08\x00\x00\x00\x00h\x01\x00\x00\x00X\x04\x14\x00D\x00\n\x05\x00\x00\x00 \x00\x00\x00\x04\x00\x00\x00\x03 \x08\x08\x00\x00\x00\x00\x01\x00\x00\x00\x05D\x01D\x01$\x00\n\x08\x00\x00\x00 \x00\x00\x00\x04\x00\x00\x00\x03 \x08\x08\x01\x00\x00\x00\x00\x00\x00\x00\x0b\x10\x05D\x06$\x06\x05\n\x00\x00\x00\x1a\x00\x00\x00\x04\x00\x00\x00\x07 \x08\x08\x00\x00\x00\x00\x00\x00\x00\x02\xff\xd7\x00\x01\x02\x00\x1a\x00\x00\x00\x04\x00\x00\x00\x07 \x08\x08\x00\x00\x00\x00\x00\x00\x00\x02\xff_\x80\x01\x02\x00\x1a\x00\x00\x00\x04\x00\x00\x00\x07 \x08\x08\x00\x00\x00\x00\x00\x00\x00\x02\x0b\x10\x01\x00\x02\x00\x12\x00\x00\x00\x04\x00\x00\x00\x00 \x08\x082\x80\x0b\x00\x00$\x12\x00\x00\x00\x04\x00\x00\x00\x00 \x08\x08\x00\x00\x00\x00\x01$\x12\x00\x00\x00\x04\x00\x00\x00\x00 \x08\x08\x01\x00\x00\x00\x02$\x12\x00\x00\x00\x04\x00\x00\x00\x00 \x08\x08\x00\x00\x00\x00\x03$\x12\x00\x00\x00\x04\x00\x00\x00\x00 \x08\x08\x00\x00\x00\x00\x05$\x12\x00\x00\x00\x04\x00\x00\x00\x00 \x08\x082\x80\x0b\x00\x06$\x0c\x00\x00\x00\x04\x00\x00\x00\x0e \x08\x08\x16\x00\x00\x00\x04\x00\x00\x00\x07*\x08\x08\x00 \x00\x00\x00\x00\x00\x00\x00\x02\x10\x00\x00\x00\x04\x00\x00\x00\x08*\x08\x08\x01\x00\x00\x00\x0c\x00\x00\x00\x04\x00\x00\x00\t*\x08\x08\x16\x00\x00\x00\x04\x00\x00\x00\x07*\x08\x082\x80\x01\x00\x00\x00\x00\x00\x00\x01\r\x00\x00\x00\x04\x00\x00\x00\x08*\x08\x08\n\x0c\x00\x00\x00\x04\x00\x00\x00\t*\x08\x08\x16\x00\x00\x00\x04\x00\x00\x00\x07*\x08\x08B\x80\x01\x00\x00\x00\x00\x00\x00\x01\x0e\x00\x00\x00\x04\x00\x00\x00\x08*\x08\x08\x90\x01\x0c\x00\x00\x00\x04\x00\x00\x00\t*\x08\x08\x16\x00\x00\x00\x04\x00\x00\x00\x07*\x08\x08P\x80\x01\x00\x00\x00\x00\x00\x00\x01\r\x00\x00\x00\x04\x00\x00\x00\x08*\x08\x08\x03\x0c\x00\x00\x00\x04\x00\x00\x00\t*\x08\x08\x16\x00\x00\x00\x04\x00\x00\x00\x07*\x08\x08Q\x80\x01\x00\x00\x00\x00\x00\x00\x01\r\x00\x00\x00\x04\x00\x00\x00\x08*\x08\x08\x08\x0c\x00\x00\x00\x04\x00\x00\x00\t*\x08\x08\x16\x00\x00\x00\x04\x00\x00\x00\x07*\x08\x08R\x80\x01\x00\x00\x00\x00\x00\x00\x01\r\x00\x00\x00\x04\x00\x00\x00\x08*\x08\x08\x08\x0c\x00\x00\x00\x04\x00\x00\x00\t*\x08\x08\x16\x00\x00\x00\x04\x00\x00\x00\x07*\x08\x08S\x80\x01\x00\x00\x00\x00\x00\x00\x01\r\x00\x00\x00\x04\x00\x00\x00\x08*\x08\x08\x08\x0c\x00\x00\x00\x04\x00\x00\x00\t*\x08\x08\x16\x00\x00\x00\x04\x00\x00\x00\x07*\x08\x08T\x80\x01\x00\x00\x00\x00\x00\x00\x01\r\x00\x00\x00\x04\x00\x00\x00\x08*\x08\x08\x08\x0c\x00\x00\x00\x04\x00\x00\x00\t*\x08\x08\x16\x00\x00\x00\x04\x00\x00\x00\x07*\x08\x08U\x80\x01\x00\x00\x00\x00\x00\x00\x01\r\x00\x00\x00\x04\x00\x00\x00\x08*\x08\x08\x08\x0c\x00\x00\x00\x04\x00\x00\x00\t*\x08\x08\x16\x00\x00\x00\x04\x00\x00\x00\x07*\x08\x08V\x80\x01\x00\x00\x00\x00\x00\x00\x01\r\x00\x00\x00\x04\x00\x00\x00\x08*\x08\x08\x08\x0c\x00\x00\x00\x04\x00\x00\x00\t*\x08\x08\x16\x00\x00\x00\x04\x00\x00\x00\x07*\x08\x08W\x80\x01\x00\x00\x00\x00\x00\x00\x01\r\x00\x00\x00\x04\x00\x00\x00\x08*\x08\x08\x08\x0c\x00\x00\x00\x04\x00\x00\x00\t*\x08\x08\x16\x00\x00\x00\x04\x00\x00\x00\x07*\x08\x08X\x80\x01\x00\x00\x00\x00\x00\x00\x01\r\x00\x00\x00\x04\x00\x00\x00\x08*\x08\x08\x08\x0c\x00\x00\x00\x04\x00\x00\x00\t*\x08\x08\x16\x00\x00\x00\x04\x00\x00\x00\x07*\x08\x08Y\x80\x01\x00\x00\x00\x00\x00\x00\x01\r\x00\x00\x00\x04\x00\x00\x00\x08*\x08\x08\x08\x0c\x00\x00\x00\x04\x00\x00\x00\t*\x08\x08\x16\x00\x00\x00\x04\x00\x00\x00\x07*\x08\x08\x01\x90\x01\x00\x00\x00\x00\x00\x00\x01\r\x00\x00\x00\x04\x00\x00\x00\x08*\x08\x08\x00\x0c\x00\x00\x00\x04\x00\x00\x00\t*\x08\x08'

    try:
        ota_updater._apply_ota_update(blob=blob)
    except:
        pytest.fail("Unexpected error")


def test_inform_cloud(ota_cloud, simple_hw):

    cloud, _proj_id, _server = ota_cloud

    hw = simple_hw
    app_tag = 123
    app_version = SemanticVersion(0,0,2)
    os_tag = 234
    os_version = SemanticVersion(0,0,2)
    app_info = [app_tag, app_version]
    os_info = [os_tag, os_version]

    device_id = 1
    hw.connect(device_id)
    ota_updater = OtaUpdater(hw, app_info, os_info, device_id)

    try:
        ota_updater._inform_cloud(device_id, 'd--0000-0000-0000-0001', True)
    except:
        pytest.fail("inform cloud test failed")


def test_all_attributes(ota_cloud, simple_hw):

    cloud, _proj_id, _server = ota_cloud

    app_tags = [122, 123, 124]
    app_versions = [SemanticVersion(0, 0, 1), SemanticVersion(0, 0, 2), SemanticVersion(0, 0, 3)]

    os_tags = [233, 234, 235]
    os_versions = [SemanticVersion(0, 0, 1), SemanticVersion(0, 0, 2), SemanticVersion(0, 0, 3)]

    devices = [1, 4, 6]
    expected_results = [False, False, False, False, False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, False, False, (3, 'bar.com/zipzap'), False, False,
                        False, False, False, False, False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, False, False, False, False, False,
                        (3, 'bar.com/zipzap'), False, False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, False, False, False, (1, 'bar.com/zipzap'), False,
                        False, False, False, False, False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, (5, 'bar.com/zipzap'), (7, 'bar.com/zipzap'),
                        (9, 'bar.com/zipzap'), False, False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, False, False, False, False, False, False, False,
                        False, (5, 'bar.com/zipzap'), (7, 'bar.com/zipzap'), (9, 'bar.com/zipzap'), False, False,
                        False, False, False, False, False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False]

    stage = 0

    for app_tag in app_tags:
        for app_version in app_versions:
            for os_tag in os_tags:
                for os_version in os_versions:
                    for device_id in devices:

                        app_info = [app_tag, app_version]
                        os_info = [os_tag, os_version]
                        hw = simple_hw
                        try:
                            hw.disconnect()
                        except:
                            pass
                        hw.connect(device_id)

                        ota_updater = OtaUpdater(hw, app_info, os_info, device_id)
                        actual_result = ota_updater.check_cloud_for_script()

                        if not actual_result:
                            print("os_tag={2}, app_tag={0}, os_version={3}, app_version={1}".format(app_tag, app_version, os_tag, os_version))
                        if actual_result:
                            print("---------")
                            print("Match achieved for device ID ", device_id)
                            print("os_tag={2}, app_tag={0}, os_version={3}, app_version={1}".format(app_tag, app_version, os_tag, os_version))
                            print("---------")

                        assert expected_results[stage] == actual_result
                        stage += 1