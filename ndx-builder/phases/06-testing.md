## Phase 6: Testing

**Goal**: Write comprehensive tests that verify the extension works correctly.

**Entry**: You have working Python classes from Phase 5.

**Exit criteria**:
- Constructor tests pass for all types
- Round-trip tests (write + read back) pass for all types
- Edge cases (optional fields, multiple instances) are covered
- All tests pass with `pytest`

### Step 1: Write Constructor Tests

Test that each type can be constructed with valid arguments and rejects invalid ones.

Edit `src/pynwb/tests/test_<name>.py`:

```python
import numpy as np
from numpy.testing import assert_array_equal
import pytest
from pynwb.testing import TestCase

from ndx_<name> import MyType, MyContainer


class TestMyTypeConstructor(TestCase):
    """Test MyType constructor."""

    def test_init_required_fields(self):
        """Test construction with only required fields."""
        obj = MyType(
            name="test",
            signal=np.random.rand(100, 3),
            sampling_rate=30.0,
        )
        assert obj.name == "test"
        assert obj.signal.shape == (100, 3)
        assert obj.sampling_rate == 30.0

    def test_init_all_fields(self):
        """Test construction with all fields including optional ones."""
        from pynwb.device import Device
        device = Device(name="my_device")

        obj = MyType(
            name="test",
            signal=np.random.rand(100, 3),
            sampling_rate=30.0,
            description="A test object",
            device=device,
        )
        assert obj.description == "A test object"
        assert obj.device is device

    def test_init_missing_required(self):
        """Test that missing required fields raise errors."""
        with pytest.raises(TypeError):
            MyType(name="test")  # Missing signal and sampling_rate


class TestMyContainerConstructor(TestCase):
    """Test MyContainer constructor."""

    def test_init_empty(self):
        """Test empty container."""
        container = MyContainer(name="test_container")
        assert len(container.my_types) == 0

    def test_init_with_items(self):
        """Test container with initial items."""
        items = [
            MyType(name="item1", signal=np.ones((10, 2)), sampling_rate=1.0),
            MyType(name="item2", signal=np.ones((10, 2)), sampling_rate=2.0),
        ]
        container = MyContainer(name="test_container", my_types=items)
        assert len(container.my_types) == 2

    def test_add_and_get(self):
        """Test adding and retrieving items."""
        container = MyContainer(name="test_container")
        item = MyType(name="item1", signal=np.ones((10, 2)), sampling_rate=1.0)
        container.add_my_type(item)
        retrieved = container.get_my_type("item1")
        assert retrieved is item
```

### Step 2: Write Round-Trip Tests

Round-trip tests verify that data survives write → read. Use `NWBH5IOMixin` from
`pynwb.testing` for a standardized pattern.

```python
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
from numpy.testing import assert_array_equal
from pynwb import NWBFile, NWBHDF5IO
from pynwb.testing import TestCase, NWBH5IOMixin

from ndx_<name> import MyType


class TestMyTypeRoundTrip(NWBH5IOMixin, TestCase):
    """Test round-trip (write + read) for MyType."""

    def setUpContainer(self):
        """Create the container to test."""
        return MyType(
            name="test_roundtrip",
            signal=np.random.rand(100, 3).astype("float64"),
            sampling_rate=30.0,
            description="Test round-trip",
        )

    def addContainer(self, nwbfile):
        """Add the container to the NWB file."""
        nwbfile.add_acquisition(self.container)

    def getContainer(self, nwbfile):
        """Retrieve the container from the NWB file after reading."""
        return nwbfile.acquisition["test_roundtrip"]

    def test_roundtrip(self):
        """Verify data integrity after round-trip."""
        # This is called automatically by NWBH5IOMixin
        # but you can add extra assertions:
        read_container = self.roundtripContainer()
        assert_array_equal(read_container.signal[:], self.container.signal)
        assert read_container.sampling_rate == self.container.sampling_rate
        assert read_container.description == self.container.description
```

**For LabMetaData types:**

```python
class TestMyMetaDataRoundTrip(NWBH5IOMixin, TestCase):

    def setUpContainer(self):
        return MyMetaData(
            name="my_metadata",
            field1="value1",
            field2=42.0,
        )

    def addContainer(self, nwbfile):
        nwbfile.add_lab_meta_data(self.container)

    def getContainer(self, nwbfile):
        return nwbfile.lab_meta_data["my_metadata"]
```

**For Device subtypes:**

```python
class TestMyDeviceRoundTrip(NWBH5IOMixin, TestCase):

    def setUpContainer(self):
        return MyDevice(
            name="test_device",
            description="A test device",
            manufacturer="Test Corp",
            serial_number="SN12345",
        )

    def addContainer(self, nwbfile):
        nwbfile.add_device(self.container)

    def getContainer(self, nwbfile):
        return nwbfile.devices["test_device"]
```

**For containers in processing modules:**

```python
class TestMyContainerRoundTrip(NWBH5IOMixin, TestCase):

    def setUpContainer(self):
        items = [
            MyType(name="item1", signal=np.ones((10, 2)), sampling_rate=1.0),
            MyType(name="item2", signal=np.ones((20, 2)), sampling_rate=2.0),
        ]
        return MyContainer(name="test_container", my_types=items)

    def addContainer(self, nwbfile):
        module = nwbfile.create_processing_module("test", "Test module")
        module.add(self.container)

    def getContainer(self, nwbfile):
        return nwbfile.processing["test"]["test_container"]
```

### Step 3: Write Edge Case Tests

```python
class TestMyTypeEdgeCases(TestCase):
    """Test edge cases."""

    def test_optional_fields_none(self):
        """Test that optional fields can be None."""
        obj = MyType(
            name="test",
            signal=np.zeros((1, 3)),
            sampling_rate=1.0,
        )
        assert obj.device is None

    def test_large_data(self):
        """Test with realistically-sized data."""
        obj = MyType(
            name="test",
            signal=np.random.rand(100000, 10),
            sampling_rate=30000.0,
        )
        assert obj.signal.shape == (100000, 10)

    def test_single_column(self):
        """Test with single-column data."""
        obj = MyType(
            name="test",
            signal=np.random.rand(100, 1),
            sampling_rate=1.0,
        )
        assert obj.signal.shape == (100, 1)
```

### Step 4: Write DynamicTable Tests (if applicable)

```python
class TestMyTableRoundTrip(NWBH5IOMixin, TestCase):

    def setUpContainer(self):
        table = MyTable(
            name="test_table",
            description="Test table",
        )
        table.add_row(location="V1", threshold=0.5)
        table.add_row(location="CA1", threshold=0.3)
        return table

    def addContainer(self, nwbfile):
        module = nwbfile.create_processing_module("test", "Test module")
        module.add(self.container)

    def getContainer(self, nwbfile):
        return nwbfile.processing["test"]["test_table"]

    def test_roundtrip_data(self):
        read_table = self.roundtripContainer()
        assert len(read_table) == 2
        assert read_table["location"][0] == "V1"
        assert read_table["threshold"][1] == 0.3
```

### Step 5: Run Tests

```bash
cd ndx-<name>
pytest src/pynwb/tests/ -v
```

If tests fail:
1. Read the error message carefully
2. Check if it's a spec issue (Phase 4) or a Python API issue (Phase 5)
3. Fix the issue
4. Re-run tests

### Step 6: Check Test Coverage

```bash
pytest src/pynwb/tests/ -v --cov=ndx_<name> --cov-report=term-missing
```

Aim for:
- 100% coverage of `__init__` methods
- 100% coverage of custom methods
- Round-trip tests for every type

### Common Test Issues

**`NWBH5IOMixin` test fails with "container not found"**: The `getContainer` method
returns the wrong path. Check that `addContainer` puts the object where `getContainer`
looks for it.

**Round-trip data mismatch**: Check data types. HDF5 may convert Python lists to
numpy arrays, or change dtype precision.

**"Namespace not loaded" error in tests**: Make sure the test file imports from the
package (`from ndx_<name> import ...`) not from internal modules directly.

**Temporary file cleanup**: `NWBH5IOMixin` handles temp file creation and cleanup
automatically. Don't create your own temp files for round-trip tests.
