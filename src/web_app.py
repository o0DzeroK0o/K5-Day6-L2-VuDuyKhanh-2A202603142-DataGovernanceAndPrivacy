"""Local HTTP workspace for the five real T02 pipeline stages.

Run: .venv/bin/python -m src.web_app --port 8765
Browser: http://127.0.0.1:8765
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import re
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pandas as pd

from .common.io import resolve_config, write_json, read_json
from .web_worker import STEPS, now, current_revision

ROOT=Path(__file__).resolve().parents[1]
ASSETS=Path(__file__).with_name('web_ui')
DOWNLOADS={'loaded_images.csv','loaded_manifest.csv','raw_predictions.csv','review_queue.csv',
           'review_queue_reviewed.csv','ranked_review.csv','item_decisions.csv','decision.json',
           'audit_log.jsonl','decision_log.csv','run_info.json','workflow.json','review_confirmation.json'}


class Conflict(ValueError):
    pass


class Workspace:
    def __init__(self,output: Path,input_dir: Path | None=None):
        self.output=output.resolve();self.output.mkdir(parents=True,exist_ok=True)
        self.input_dir=(input_dir or ROOT/'fixtures/t02_raw_qc').resolve()
        self.locks={};self.guard=threading.Lock()

    def run_dir(self,ident):
        if not re.fullmatch(r'[0-9a-f]{32}',ident):
            raise FileNotFoundError('Không tìm thấy lượt chạy.')
        path=self.output/ident
        if not (path/'current.json').is_file():
            raise FileNotFoundError('Không tìm thấy lượt chạy.')
        return path

    def lock(self,ident):
        with self.guard:return self.locks.setdefault(ident,threading.RLock())

    def create(self):
        ident=uuid.uuid4().hex;run=self.output/ident;revision=run/'revisions/000000'
        revision.mkdir(parents=True)
        cfg=resolve_config(ROOT/'configs/lab.yaml')
        cfg['human_review_confirmed']=False
        cfg['offline']=True
        stamp=now()
        state={'run_id':ident,'revision':0,'created_at':stamp,'updated_at':stamp,'input_dir':str(self.input_dir),
               'dataset':self.input_dir.name,'owner':cfg['owner'],'human_confirmed':False,'steps':{s:{'done':False} for s in STEPS},
               'stats':{},'history':[],'decision':None,'review_source':None}
        write_json(revision/'config.json',cfg);write_json(revision/'workflow.json',state)
        write_json(run/'current.json',{'revision':0})
        return self.snapshot(ident)

    def listing(self):
        result=[]
        for directory in self.output.iterdir():
            if not re.fullmatch(r'[0-9a-f]{32}',directory.name) or not (directory/'current.json').exists():continue
            _,current=current_revision(directory)
            state=read_json(current/'workflow.json')
            result.append({k:state[k] for k in ('run_id','created_at','revision','updated_at','decision')})
        return sorted(result,key=lambda r:r['created_at'],reverse=True)

    def snapshot(self,ident):
        with self.lock(ident):
            _,directory=current_revision(self.run_dir(ident))
            state=read_json(directory/'workflow.json')
            for name,key in [('loaded_images.csv','images'),('raw_predictions.csv','features'),
                             ('review_queue.csv','queue'),('review_queue_reviewed.csv','reviews')]:
                path=directory/name
                # Keep notes, IDs and reviewer names textual even when their
                # values happen to look numeric (CSV inference loses leading 0s).
                dtype=str if key in ('images','queue','reviews') else None
                state[key]=json.loads(pd.read_csv(path,keep_default_na=False,dtype=dtype).to_json(orient='records',double_precision=15)) if path.exists() else []
            state['downloads']=[f for f in sorted(DOWNLOADS) if (directory/f).is_file()]
            audit=directory/'audit_log.jsonl'
            state['audit']=[json.loads(line) for line in audit.read_text().splitlines() if line] if audit.exists() else []
            return state

    def stage(self,ident,stage,payload):
        with self.lock(ident):
            directory=self.run_dir(ident)
            revision,_=current_revision(directory)
            if type(payload.get('revision')) is not int or payload['revision']!=revision:
                raise Conflict('Dữ liệu đã thay đổi. Bấm Tải lại để lấy phiên bản mới nhất.')
            if stage not in STEPS:raise ValueError('Bước pipeline không hợp lệ.')
            process=subprocess.run([sys.executable,'-m','src.web_worker','--run-dir',str(directory),'--stage',stage],
                input=json.dumps(payload,ensure_ascii=False),text=True,capture_output=True,cwd=ROOT,timeout=120)
            if process.returncode:
                try:message=json.loads(process.stdout.strip().splitlines()[-1])['error']
                except (ValueError,IndexError,KeyError):message='Không hoàn tất bước xử lý. Kiểm tra log máy chủ.'
                if process.stderr:print(process.stderr,file=sys.stderr)
                raise ValueError(message)
            return self.snapshot(ident)

    def artifact(self,ident,name):
        if name not in DOWNLOADS:raise FileNotFoundError('Không có artifact này.')
        _,directory=current_revision(self.run_dir(ident))
        path=directory/name
        if not path.is_file():raise FileNotFoundError('Chưa tạo artifact; hãy chạy bước tương ứng.')
        return path

    def image(self,ident,item_id):
        from .pipeline import _inside
        _,directory=current_revision(self.run_dir(ident))
        if not (directory/'loaded_images.csv').exists():raise FileNotFoundError('Chưa Load dữ liệu.')
        data=pd.read_csv(directory/'loaded_images.csv',dtype=str)
        row=data.loc[data.image_id==item_id]
        if len(row)!=1:raise FileNotFoundError('Không có ảnh này trong lượt chạy.')
        state=read_json(directory/'workflow.json')
        return _inside(Path(state['input_dir']),row.iloc[0].path)


def handler_for(workspace):
    class Handler(BaseHTTPRequestHandler):
        server_version='QCWorkspace/1.0'

        def log_message(self,format,*args):
            # Do not log request bodies, notes, or user identity.
            if args and str(args[1] if len(args)>1 else '') not in ('200','201'):
                super().log_message(format,*args)

        def send_bytes(self,data,content_type,status=200,filename=None):
            self.send_response(status)
            self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','same-origin')
            if filename:self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
            self.end_headers();self.wfile.write(data)

        def json(self,value,status=200):
            self.send_bytes(json.dumps(value,ensure_ascii=False,allow_nan=False).encode(),'application/json; charset=utf-8',status)

        def route(self):
            port=self.server.server_port
            allowed={f'127.0.0.1:{port}',f'localhost:{port}'}
            if self.headers.get('Host') not in allowed:
                self.json({'error':'Host không hợp lệ.'},403);return
            path=unquote(urlsplit(self.path).path)
            if self.command=='POST':
                origin=self.headers.get('Origin')
                if (origin and origin not in {f'http://{host}' for host in allowed}) or self.headers.get('X-QC-Request')!='workspace':
                    self.json({'error':'Yêu cầu phải gửi từ giao diện cùng máy chủ.'},403);return
                if self.headers.get_content_type()!='application/json':raise ValueError('Yêu cầu cần JSON.')
                length=int(self.headers.get('Content-Length','0'))
                if length<=0 or length>1_000_000:raise ValueError('Kích thước yêu cầu không hợp lệ.')
                payload=json.loads(self.rfile.read(length))
                if not isinstance(payload,dict):raise ValueError('Yêu cầu JSON cần là object.')
                if path=='/api/runs':self.json(workspace.create(),201);return
                match=re.fullmatch(r'/api/runs/([0-9a-f]{32})/steps/(load|process|rank|review|decide)',path)
                if match:self.json(workspace.stage(match[1],match[2],payload));return
            else:
                if path=='/api/runs':self.json(workspace.listing());return
                if path in ('/','/app.css','/app.js'):
                    name={'/':'index.html','/app.css':'app.css','/app.js':'app.js'}[path]
                    self.send_bytes((ASSETS/name).read_bytes(),mimetypes.guess_type(name)[0]+'; charset=utf-8');return
                match=re.fullmatch(r'/api/runs/([0-9a-f]{32})',path)
                if match:self.json(workspace.snapshot(match[1]));return
                match=re.fullmatch(r'/api/runs/([0-9a-f]{32})/images/([A-Za-z0-9_.-]+)',path)
                if match:
                    image=workspace.image(match[1],match[2]);self.send_bytes(image.read_bytes(),'image/jpeg');return
                match=re.fullmatch(r'/api/runs/([0-9a-f]{32})/files/([a-z_.]+)',path)
                if match:
                    artifact=workspace.artifact(match[1],match[2])
                    self.send_bytes(artifact.read_bytes(),mimetypes.guess_type(artifact.name)[0] or 'application/octet-stream',filename=artifact.name);return
            raise FileNotFoundError('Không tìm thấy đường dẫn.')

        def handle_request(self):
            try:self.route()
            except Conflict as error:self.json({'error':str(error)},409)
            except FileNotFoundError as error:self.json({'error':str(error)},404)
            except (ValueError,KeyError,TypeError) as error:self.json({'error':str(error)},400)
            except subprocess.TimeoutExpired:self.json({'error':'Xử lý quá thời gian. Tải lại để kiểm tra trạng thái trước khi thử lại.'},504)
            except (BrokenPipeError,ConnectionResetError):pass
            except Exception as error:
                print(type(error).__name__,str(error),file=sys.stderr)
                self.json({'error':'Lỗi máy chủ. Tải lại để kiểm tra trạng thái; xem log để xử lý.'},500)

        do_GET=handle_request
        do_POST=handle_request
    return Handler


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--output',type=Path,default=ROOT/'out/web')
    args=parser.parse_args()
    workspace=Workspace(args.output)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),handler_for(workspace))
    server.daemon_threads=True
    print(f'QC Workspace: http://127.0.0.1:{server.server_port}',flush=True)
    print(f'Kết quả và lịch sử: {workspace.output}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
