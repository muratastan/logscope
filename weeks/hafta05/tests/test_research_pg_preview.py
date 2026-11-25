from pathlib import Path
from tempfile import TemporaryDirectory
from backend.research_pg import preview_import,read_manifest
from scripts.week3_generate_dataset import make_offline_events

def test_can_prepare_canonical_import_with_external_labels():
    with TemporaryDirectory() as temp:
        o=make_offline_events(120,35,31,temp)
        summary,manifest,stats,sessions=preview_import(o['data_file'],o['labels_file'])
        assert summary['events']==o['total_requests']
        assert summary['minutes_with_events']==120
        assert summary['truth_kept_out_of_log']
        assert len(stats)==len(manifest)
        assert len(sessions)>0
