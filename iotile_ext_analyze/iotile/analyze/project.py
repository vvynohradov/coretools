"""The AnalysisProject is the main entry point for analyzing data.

It allows you to select data streams from IOTile.cloud and turn them
into Pandas time series for analysis.
"""

import pandas as pd
from iotile.cloud import IOTileCloud
from iotile.core.exceptions import ArgumentError, ExternalError
from iotile_cloud.api.exceptions import RestHttpBaseException
from iotile_cloud.stream.data import StreamData

class AnalysisProject(object):
    """A top level entry point for selecting and analyzing data.

    Currently AnalysisProjects must be created by passing the id
    or slug of a project in iotile.cloud and then are populated with
    all of the data streams in that project.

    If you specify 'device' for source_type, the cloud_id should be
    a slug for the device that you want to fetch streams from.

    if you specify 'project' for source type, the cloud_id should be
    the UUId of the project that you want to fetch streams from.

    Args:
        cloud_id (str): An IOTile.cloud id (usually a slug) that
            selects that data streams are included in this analysis
            project.
        source_type (str): The type of iotile.cloud object that we
            are linking this AnalysisProject to.  This defaults to
            an iotile.cloud project, but finding only streams from a
            single device is also supported.  You can currently
            specify either 'project' or device.
    """

    def __init__(self, cloud_id, source_type='project'):
        stream_finders = {
            'project': self._find_project_streams,
            'device': self._find_device_streams
        }

        stream_finder = stream_finders.get(source_type, None)
        if stream_finder is None:
            raise ArgumentError("Invalid source type", source_type=source_type, supported_sources=stream_finders.keys())

        self._cloud = IOTileCloud()

        stream_list = stream_finder(cloud_id)
        self.streams = self._parse_stream_list(stream_list)

    def fetch_stream(self, slug):
        """Fetch data from a stream by its slug.

        Args:
            slug (str): The stream slug that we want to fetch
        """

        data = self._get_stream_data(slug)

        dt_index = pd.to_datetime([x['timestamp'] for x in data])
        return pd.Series([x['output_value'] for x in data], index=dt_index)

    def _find_project_streams(self, project_id):
        """Find all streams in a project by its uuid."""

        try:
            results = self._cloud.api.stream.get(project=project_id)
            return results['results']
        except RestHttpBaseException as exc:
            raise ExternalError("Error calling method on iotile.cloud", exception=exc, response=exc.response.status_code)

    def _find_device_streams(self, device_slug):
        """Find all streams for a device by its slug."""

        try:
            results = self._cloud.api.stream.get(device=device_slug)
            return results['results']
        except RestHttpBaseException as exc:
            raise ExternalError("Error calling method on iotile.cloud", exception=exc, response=exc.response.status_code)

    @classmethod
    def _parse_stream_list(cls, stream_list):
        return {stream['slug']: stream for stream in stream_list}

    def _get_stream_data(self, slug, start=None, end=None):
        fetcher = StreamData(slug, self._cloud.api)

        fetcher.initialize_from_server()
        return fetcher._data
