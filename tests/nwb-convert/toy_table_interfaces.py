from hdmf.common import MeaningsTable
from neuroconv import BaseDataInterface
from pynwb.event import EventsTable


class TablesInterface(BaseDataInterface):
    """Adds a trials table and an events table whose columns hold coded values."""

    def __init__(self, events: bool = True):
        super().__init__(events=events)
        self.events = events

    def add_to_nwbfile(self, nwbfile, metadata, **kwargs):
        nwbfile.add_trial_column(name="result", description="Result of the trial.")
        nwbfile.add_trial_column(name="ctr_hold_bump", description="Whether there was a bump during center hold.")
        nwbfile.add_trial_column(name="split", description="The benchmark split of the trial.")
        nwbfile.add_trial_column(name="stimulus_code", description="The code of the stimulus shown.")
        nwbfile.add_trial_column(name="target_dir", description="Direction of the target, in degrees.")
        nwbfile.add_trial_column(name="note", description="Free-text note on the trial.")
        rows = [
            ("R", True, "train", 1, 0.0, "clean"),
            ("A", False, "val", 2, 45.0, "left early"),
            ("R", True, "train", 1, 90.0, "slow"),
            ("R", False, "train", 2, 135.5, "good"),
        ]
        for index, (result, bump, split, code, direction, note) in enumerate(rows):
            nwbfile.add_trial(
                start_time=float(index), stop_time=index + 0.5, result=result, ctr_hold_bump=bump, split=split,
                stimulus_code=code, target_dir=direction, note=note,
            )
        if not self.events:
            return
        # An events table as a NeuroConv events interface writes it: the types it was given a
        # description for already have a row in the event_type MeaningsTable.
        events = EventsTable(name="TaskEvents", description="Events of the task.")
        events.add_column(name="event_type", description="The event type of each event.")
        for timestamp, event_type in [(0.1, "go_cue"), (0.4, "reward"), (1.1, "go_cue")]:
            events.add_row(timestamp=timestamp, event_type=event_type)
        meanings_table = MeaningsTable(target=events["event_type"], description="Meaning of each event type.")
        meanings_table.add_row(value="go_cue", meaning="The go cue as the interface described it.")
        events.add_meanings_table(meanings_table)
        nwbfile.add_events_table(events)


INTERFACES = dict(Tables=TablesInterface)
