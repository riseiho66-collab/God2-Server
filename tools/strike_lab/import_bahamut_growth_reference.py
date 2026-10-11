"""Read owner-selected public wiki tables into a provenance-bearing SQLite catalog.

Reference data only: no player saves, native IDs or wild-monster stats inferred.
Each source table retains unknown cells and stated generation/level scope.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import unicodedata
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[2]
PAGES={
 'general-pet-growth':('一般地圖戰寵升級配點資料','FIRST_GENERATION'),
 'jiuli-pet-growth':('九黎全島戰寵升級配點資料','FIRST_GENERATION'),
 'frost-pet-growth':('冰霜高地戰寵升級配點資料','FIRST_GENERATION'),
 'other-pet-growth':('其他類戰寵升級配點資料','FIRST_GENERATION'),
 'second-pet-growth':('二代戰寵升級配點資料','SECOND_GENERATION'),
 'transformed-pet-growth':('轉世戰寵升級配點資料','TRANSFORMED_PET'),
 'transformed-other-growth':('轉世其他類升級配點資料','TRANSFORMED_PET'),
}

class Tables(HTMLParser):
 def __init__(self):
  super().__init__();self.stack=[];self.tables=[];self.expanded_tables=[];self.contexts=[];self.heading=None;self.last_heading=''
 def handle_starttag(self,tag,attrs):
  if tag in ('h2','h3'):self.heading=[]
  if tag=='table':self.stack.append({'rows':[],'spans':[],'cell':None,'row':None,'context':self.last_heading})
  elif self.stack:
   t=self.stack[-1]
   if tag=='tr':t['row']=[];t['row_spans']=[]
   elif tag in ('td','th'):
    t['cell']=[];a=dict(attrs);t['cell_span']=(int(a.get('rowspan','1')),int(a.get('colspan','1')))
   elif tag=='br' and t['cell'] is not None:t['cell'].append('\n')
 def handle_data(self,data):
  if self.heading is not None:self.heading.append(data)
  if self.stack and self.stack[-1]['cell'] is not None:self.stack[-1]['cell'].append(data)
 def handle_endtag(self,tag):
  if tag in ('h2','h3') and self.heading is not None:
   self.last_heading=''.join(self.heading).strip();self.heading=None
  if not self.stack:return
  t=self.stack[-1]
  if tag in ('td','th') and t['cell'] is not None:
   if t['row'] is not None:
    t['row'].append(''.join(t['cell']).strip());t['row_spans'].append(t['cell_span'])
   t['cell']=None
  elif tag=='tr' and t['row'] is not None:
   t['rows'].append(t['row']);t['spans'].append(t['row_spans']);t['row']=None
  elif tag=='table':
   t=self.stack.pop();self.tables.append(t['rows']);self.contexts.append(t['context']);grid={};expanded=[]
   for ri,(row,spans) in enumerate(zip(t['rows'],t['spans'])):
    ci=0
    for value,(height,width) in zip(row,spans):
     while (ri,ci) in grid:ci+=1
     if not 1<=height<=200 or not 1<=width<=200:raise ValueError('Invalid table span')
     for dy in range(height):
      for dx in range(width):
       pos=(ri+dy,ci+dx)
       if pos in grid:raise ValueError('Overlapping table spans')
       grid[pos]=value
     ci+=width
    last=max((c for r,c in grid if r==ri),default=-1)
    expanded.append([grid.get((ri,c),'') for c in range(last+1)])
   self.expanded_tables.append(expanded)

def growth(text):
 value=re.sub(r'\s+','',unicodedata.normalize('NFKC',text))
 if not value or value=='未知':return None
 tokens=re.findall(r'(\d+)([體力智速])',value)
 if not tokens or ''.join(a+b for a,b in tokens)!=value:return None
 result=[0,0,0,0]
 for number,kind in tokens:
  index='體力智速'.index(kind)
  if result[index]:raise ValueError('Duplicate stat token')
  result[index]=int(number)
 return result

def capture(item,out):
 key,(title,generation)=item
 from urllib.parse import quote
 url='https://wiki2.gamer.com.tw/wiki.php?n=8591:'+quote(title)+'&ss=8591&f=M'
 path=out/(key+'.html')
 if not path.exists():
  raw=urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read()
  path.write_bytes(raw)
 raw=path.read_bytes();text=raw.decode('utf-8')
 if title not in text or 'BH-master' not in text:raise ValueError('Unexpected public page '+key)
 parser=Tables();parser.feed(text)
 return key,title,generation,url,hashlib.sha256(raw).hexdigest(),parser.tables,parser.expanded_tables,parser.contexts

def numeric(text):
 text=unicodedata.normalize('NFKC',text).strip()
 return int(text) if re.fullmatch(r'\d+',text) else None

def profiles(rows,expanded,context=''):
 """Separate layouts and generations; retain literal range labels, including typos."""
 if not rows:return []
 header=[unicodedata.normalize('NFKC',x) for x in rows[0]]
 result=[]
 if len(header)==9 and header[0]=='戰寵類別':
  for row in rows[1:]:
   if len(row)==9:
    result.append((row[0],'破頂' if '必破頂' in row[1] else '',row[1],header[2:5],[growth(x) for x in row[2:5]],{'99':[numeric(x) for x in row[5:9]]}))
 elif len(header)==9 and header[4]=='LV':
  family=next((r[1] for r in rows if len(r)==2 and r[0]=='戰寵名稱'),'')
  bands={};checkpoints={}
  for row in expanded[1:]:
   if len(row)!=9 or numeric(row[4]) is None:continue
   for label,value in zip(header[:4],row[:4]):
    # The fourth band may change at 125; retain each checkpoint's literal
    # source label and value rather than inventing its later range.
    bands.setdefault(label,[])
    pair={'observed_at_level':numeric(row[4]),'increment':growth(value)}
    if pair not in bands[label]:bands[label].append(pair)
   checkpoints[str(numeric(row[4]))]=[numeric(x) for x in row[5:9]]
  result.append((family,'','Source rowspan changes retained; later range requires qualification',list(bands),bands,checkpoints))
 elif header==['戰寵型態','等級','體力','力量','智力','速度']:
  current=None
  for ri,row in enumerate(expanded[1:],1):
   if len(row)!=6:continue
   match=re.fullmatch(r'LV(\d+)',unicodedata.normalize('NFKC',row[1]).replace(' ',''))
   if match:
    if current is None or current[1]!=row[0]:
     current=[context,row[0],'Page heading grouping; native species ID remains unqualified',[],[],{}];result.append(current)
    current[5][match.group(1)]=[numeric(x) for x in row[2:6]]
   elif current is not None and all('～' in x for x in row):
    current[3]=[unicodedata.normalize('NFKC',x) for x in row]
    if ri+1<len(expanded):current[4]=[growth(x) for x in expanded[ri+1]]
 return result

def checkpoint_check(profile):
 """Arithmetic consistency only; does not certify client IDs or later boundaries."""
 family,variant,notes,ranges,stages,points=profile
 if ranges[:3]!=['1~19級','20~49級','50~99級'] or not isinstance(stages,list):return None
 if len(stages)<3 or any(x is None for x in stages[:3]):return None
 baseline,expected=points.get('1'),points.get('99')
 if not baseline or not expected or any(x is None for x in baseline+expected):return None
 calculated=[baseline[i]+sum(n*stage[i] for n,stage in zip((18,30,50),stages[:3])) for i in range(4)]
 return {'basis':'Level1 checkpoint plus 18/30/50 increments; consistency hypothesis only',
         'family':family,'variant':variant,'calculated_level99':calculated,'listed_level99':expected,'matches':calculated==expected}

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,
  default=ROOT/'artifacts/research/bahamut-growth-20260927');a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
 sources=list(ThreadPoolExecutor(max_workers=4).map(lambda i:capture(i,out),PAGES.items()))
 dbpath=out/'growth-reference.db';db=sqlite3.connect(dbpath)
 db.executescript('''CREATE TABLE IF NOT EXISTS sources(key TEXT PRIMARY KEY,title TEXT NOT NULL,generation TEXT NOT NULL,url TEXT NOT NULL,sha256 TEXT NOT NULL,origin TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS pet_growth_rows(source_key TEXT NOT NULL,table_index INTEGER NOT NULL,row_index INTEGER NOT NULL,family TEXT NOT NULL,grade TEXT NOT NULL,raw_cells TEXT NOT NULL,parsed_stages TEXT NOT NULL,level99_reference TEXT NOT NULL,runtime_eligible INTEGER NOT NULL CHECK(runtime_eligible=0),PRIMARY KEY(source_key,table_index,row_index));
 CREATE TABLE IF NOT EXISTS character_growth(class_id INTEGER PRIMARY KEY,code TEXT NOT NULL,constitution INTEGER NOT NULL,strength INTEGER NOT NULL,intelligence INTEGER NOT NULL,speed INTEGER NOT NULL,manual_points INTEGER NOT NULL,first_awarded_level INTEGER NOT NULL,origin TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS pet_growth_profiles(source_key TEXT NOT NULL,table_index INTEGER NOT NULL,profile_index INTEGER NOT NULL,family TEXT NOT NULL,variant TEXT NOT NULL,notes TEXT NOT NULL,raw_ranges TEXT NOT NULL,stages TEXT NOT NULL,checkpoints TEXT NOT NULL,runtime_eligible INTEGER NOT NULL CHECK(runtime_eligible=0),PRIMARY KEY(source_key,table_index,profile_index));
 ''')
 counts={};profile_counts={};unknown=complete=0;checkpoint_checks=[]
 with db:
  for key,title,generation,url,digest,tables,expanded,contexts in sources:
   db.execute('INSERT OR REPLACE INTO sources VALUES(?,?,?,?,?,?)',(key,title,generation,url,digest,'EXTERNAL_BAHAMUT_TABLE'))
   db.execute('DELETE FROM pet_growth_rows WHERE source_key=?',(key,));count=0
   db.execute('DELETE FROM pet_growth_profiles WHERE source_key=?',(key,));profile_count=0
   for ti,rows in enumerate(tables):
    for pi,profile in enumerate(profiles(rows,expanded[ti],contexts[ti])):
     family,variant,notes,ranges,stages,checkpoints=profile
     db.execute('INSERT INTO pet_growth_profiles VALUES(?,?,?,?,?,?,?,?,?,0)',(key,ti,pi,family,variant,notes,json.dumps(ranges,ensure_ascii=False),json.dumps(stages,ensure_ascii=False),json.dumps(checkpoints)))
     profile_count+=1
     check=checkpoint_check(profile)
     if check is not None:checkpoint_checks.append({'source':key,'table_index':ti,'profile_index':pi,**check})
    # Qualify this exact eight/nine-column first-generation style. Preserve other
    # generations' raw pages for a separate parser; never squeeze them into it.
    if not rows or not any('１９級配點' in x for x in rows[0]):continue
    family=rows[1][0] if len(rows)>1 and len(rows[1])==1 else ''
    if not family:continue
    for ri,row in enumerate(rows[2:],2):
     if len(row)!=8 or row[0] not in ('普','頂','晚破','破頂'):continue
     stages=[growth(x) for x in row[1:4]]
     finals=[int(x) if re.fullmatch(r'\d+',x) else None for x in row[4:8]]
     unknown+=sum(x is None for x in stages);complete+=all(x is not None for x in stages)
     db.execute('INSERT INTO pet_growth_rows VALUES(?,?,?,?,?,?,?,?,0)',(key,ti,ri,family,row[0],json.dumps(row,ensure_ascii=False),json.dumps(stages),json.dumps(finals)))
     count+=1
   counts[key]=count
   profile_counts[key]=profile_count
  for row in [(1,'Swordsman',2,3,0,1),(2,'Taoist',1,0,3,2),(3,'Pharmacist',2,0,2,2),(4,'Warlock',1,1,1,3)]:
   db.execute('INSERT OR REPLACE INTO character_growth VALUES(?,?,?,?,?,?,4,2,?)',(*row,'OWNER_CONFIRMED_20260927'))
 assert db.execute('pragma integrity_check').fetchone()==('ok',)
 assert db.execute('select count(*) from character_growth').fetchone()[0]==4
 report={'counts':counts,'additional_layout_profiles':profile_counts,'parsed_pet_rows':sum(counts.values()),'parsed_additional_profiles':sum(profile_counts.values()),'complete_three_band_rows':complete,'unknown_stage_cells':unknown,'character_growth_rules':4,'runtime_eligible_pet_rows':0,'source_pages':7,'catalog':str(dbpath),'missing':'Qualified species ID/grade binding, award boundaries and current-client generation acceptance; unknown cells and inconsistent literal range labels retained.'}
 db.close();(out/'import-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
 (out/'checkpoint-checks.json').write_text(json.dumps({'scope':'External reference arithmetic only; not native formula or runtime acceptance',
  'checked':len(checkpoint_checks),'matched':sum(x['matches'] for x in checkpoint_checks),'checks':checkpoint_checks},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
