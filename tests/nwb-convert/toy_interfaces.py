from neuroconv import BaseDataInterface
from neuroconv.tools.testing.mock_interfaces import MockImagingInterface, MockPoseEstimationInterface, MockRecordingInterface
from pynwb.ophys import OpticalChannel


class ExtrasInterface(BaseDataInterface):
    """Adds objects with an anatomical location that NeuroConv's mock interfaces do not write."""

    def __init__(self, fiber_photometry: bool = True):
        super().__init__(fiber_photometry=fiber_photometry)
        self.fiber_photometry = fiber_photometry

    def add_to_nwbfile(self, nwbfile, metadata, **kwargs):
        device = nwbfile.create_device(name="extras_device", description="d")
        nwbfile.create_electrode_group(name="shank1", description="d", location="CA1", device=device)
        nwbfile.create_electrode_group(name="emg", description="d", location="gastrocnemius", device=device)
        nwbfile.create_imaging_plane(
            name="plane_v1", description="d", device=device, excitation_lambda=920.0, indicator="GCaMP6f",
            location="VISp", optical_channel=OpticalChannel(name="oc", description="d", emission_lambda=510.0),
        )
        nwbfile.create_icephys_electrode(name="patch", description="d", device=device, location="PL")
        nwbfile.create_ogen_site(name="ogen_site", device=device, description="d", excitation_lambda=473.0, location="VTA")
        if not self.fiber_photometry:
            return
        from ndx_fiber_photometry import FiberPhotometry, FiberPhotometryIndicators, FiberPhotometryTable
        from ndx_ophys_devices import (
            BandOpticalFilter, DichroicMirror, ExcitationSource, FiberInsertion, Indicator, OpticalFiber, Photodetector,
        )

        source = ExcitationSource(name="src", description="d", manufacturer="m")
        detector = Photodetector(name="det", description="d", manufacturer="m")
        insertion = FiberInsertion(name="fiber_insertion", depth_in_mm=3.5)
        fiber = OpticalFiber(name="fiber", description="d", manufacturer="m", fiber_insertion=insertion)
        mirror = DichroicMirror(name="mirror", description="d", manufacturer="m")
        emission = BandOpticalFilter(name="filt", description="d", manufacturer="m")
        for device in (source, detector, fiber, mirror, emission):
            nwbfile.add_device(device)
        indicator = Indicator(name="dLight", description="d", label="dLight1.1")
        table = FiberPhotometryTable(name="FiberPhotometryTable", description="d")
        for wavelength in (465.0, 405.0):
            table.add_row(location="DMS", excitation_wavelength_in_nm=wavelength, emission_wavelength_in_nm=525.0,
                          indicator=indicator, optical_fiber=fiber, excitation_source=source, photodetector=detector,
                          dichroic_mirror=mirror, emission_filter=emission)
        nwbfile.add_lab_meta_data(FiberPhotometry(
            name="fiber_photometry", fiber_photometry_table=table,
            fiber_photometry_indicators=FiberPhotometryIndicators(indicators=[indicator]),
        ))


INTERFACES = dict(Recording=MockRecordingInterface, Imaging=MockImagingInterface, Extras=ExtrasInterface, Pose=MockPoseEstimationInterface)
