import pytest
from src.adapters.counselor_adapter import CounselorJobAdapter
from src.db import JobDatabase

def test_baidu_search_snippets_fetch():
    adapter = CounselorJobAdapter()
    snippets = adapter.fetch_baidu_search_snippets(province="浙江", city="杭州")
    assert len(snippets) > 0
    assert "title" in snippets[0]
    assert "snippet" in snippets[0]

def test_counselor_announcements_baidu_and_llm_flow():
    adapter = CounselorJobAdapter()
    timestamp = "2026-07-24 14:00:00"
    anns = adapter.fetch_university_counselor_announcements(province="浙江", city="杭州", batch_timestamp=timestamp)
    
    assert len(anns) > 0
    for item in anns:
        assert item.province in ["浙江", "all"] or "浙江" in item.province
        assert item.fetched_at == timestamp

def test_counselor_announcements_db_saving(tmp_path):
    db_file = str(tmp_path / "test_jobhunter.db")
    db = JobDatabase(db_path=db_file)
    
    adapter = CounselorJobAdapter()
    timestamp = "2026-07-24 14:00:00"
    anns = adapter.fetch_university_counselor_announcements(province="all", city="all", batch_timestamp=timestamp)
    
    saved_count = db.save_counselor_announcements(anns, batch_timestamp=timestamp)
    assert saved_count == len(anns)
    
    db_anns = db.get_all_counselor_announcements()
    assert len(db_anns) == saved_count
