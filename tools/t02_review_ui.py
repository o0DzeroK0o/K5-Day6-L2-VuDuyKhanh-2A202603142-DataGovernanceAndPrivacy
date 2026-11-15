"""Build the offline review workspace from the current reviewed CSV."""
import argparse
from pathlib import Path

import pandas as pd

from src.common.contact_sheet import render_contact_sheet


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue',type=Path,default=Path('reports/review_queue.csv'))
    parser.add_argument('--output',type=Path,default=Path('reports/contact_sheet.html'))
    args=parser.parse_args()
    queue=pd.read_csv(args.queue,dtype=str).fillna('')
    render_contact_sheet(queue,args.output,image_root='fixtures/t02_raw_qc',title='T004 / T02 · Vũ Duy Khanh · 20 frame đã xác nhận')
    print(f'Review workspace: {args.output} ({len(queue)} frames)')


if __name__=='__main__':
    main()
