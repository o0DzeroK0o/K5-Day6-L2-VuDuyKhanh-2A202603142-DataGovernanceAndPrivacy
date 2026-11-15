"""Offline workspace: portable images, safe data, and shared review contract."""
import json
import re
from html.parser import HTMLParser

import pandas as pd
import pytest
from PIL import Image

from src.common.contact_sheet import render_contact_sheet
from src.common.review import REVIEW_COLUMNS


class Elements(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.elements=[]; self.feed(text)
    def handle_starttag(self, tag, attrs):
        self.elements.append((tag,dict(attrs)))


def queue():
    return pd.DataFrame([{k:'' for k in REVIEW_COLUMNS} | {'item_id':'image-1','rank':1,'score':0.8,
        'evidence_path':'image.jpg','suggested_action':'RECAPTURE','reviewer':'Vũ Duy Khanh',
        'reviewer_decision':'approve','review_note':'Mờ, mất nét.','reviewed_at':'2026-11-15T03:00:00Z'}])


def test_portable_queue_retains_saved_values_and_before_after_boxes(tmp_path):
    Image.new('RGB',(80,40),'white').save(tmp_path/'image.jpg')
    q=queue();q['before']='image.jpg'
    path=render_contact_sheet(q,tmp_path/'review.html',image_root=tmp_path,before_image_col='before',
        boxes_by_item={'image-1':[dict(x=5,y=5,w=20,h=10,label='roi')]},fields=['item_id','score'])
    text=path.read_text();elements=Elements(text)
    images=[attrs for tag,attrs in elements.elements if tag=='img' and attrs.get('src')]
    assert len(images)==2 and all(i['src'].startswith('data:image/jpeg;base64,') for i in images)
    assert all(i['alt'] for i in images)
    data=json.loads(re.search(r'<script id="queue-data" type="application/json">(.*?)</script>',text,re.S)[1])
    assert data[0]['reviewer']=='Vũ Duy Khanh' and data[0]['review_note']=='Mờ, mất nét.'
    assert data[0]['reviewer_decision']=='approve'
    assert 'NaN' not in text and not re.search(r'(?:src|href)="https?://',text)


def test_untrusted_metadata_cannot_close_json_script_or_create_markup(tmp_path):
    q=queue();payload='</script><img src=x onerror="alert(1)"> & __CSS__'
    q.loc[0,'review_note']=payload;q.loc[0,'item_id']=payload;q.loc[0,'evidence_path']=''
    q.loc[0,'reason']=float('nan')
    text=render_contact_sheet(q,tmp_path/'review.html',title=payload).read_text()
    elements=Elements(text)
    assert sum(tag=='script' for tag,_ in elements.elements)==2
    assert not any('onerror' in attrs for _,attrs in elements.elements)
    data=json.loads(re.search(r'<script id="queue-data" type="application/json">(.*?)</script>',text,re.S)[1])
    assert data[0]['review_note']==payload and data[0]['reason']==''


def test_nonembedded_image_paths_are_escaped_and_missing_images_explained(tmp_path):
    name='image".jpg';Image.new('RGB',(80,40)).save(tmp_path/name)
    q=queue();q.loc[0,'evidence_path']=name
    text=render_contact_sheet(q,tmp_path/'sub/page.html',image_root=tmp_path,embed=False).read_text()
    attrs=next(attrs for tag,attrs in Elements(text).elements if tag=='img' and attrs.get('src'))
    assert attrs['src']=='../'+name
    q.loc[0,'evidence_path']='missing.jpg'
    assert 'Không tìm thấy ảnh' in render_contact_sheet(q,tmp_path/'missing.html',image_root=tmp_path).read_text()


def test_duplicate_ids_are_rejected(tmp_path):
    with pytest.raises(ValueError,match='unique item_id'):
        render_contact_sheet(pd.concat([queue(),queue()]),tmp_path/'review.html')
