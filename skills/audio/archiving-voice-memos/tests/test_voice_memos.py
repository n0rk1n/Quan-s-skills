import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1] / 'scripts/voice_memos.py'
def atom(t,p,extended=False):
 return (struct.pack('>I4sQ',1,t,len(p)+16) if extended else struct.pack('>I4s',len(p)+8,t))+p
def fixture(text='原文。'):
 obj={'locale':{'identifier':'zh_CN'},'attributedString':{'runs':[text,0],'attributeTable':[{'timeRange':[0,1]}]}}
 return atom(b'ftyp',b'M4A ')+atom(b'mdat',b'{"fake":"audio"}',True)+atom(b'moov',atom(b'trak',atom(b'udta',atom(b'tsrp',json.dumps(obj,ensure_ascii=False).encode()))))
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if SCRIPT.exists():
   spec=importlib.util.spec_from_file_location('vm',SCRIPT);cls.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.m)
  else:cls.m=None
 def need(self):self.assertIsNotNone(self.m,'Reusable parser/export/verification helper is missing')
 def test_shifted_metadata_and_extended_audio(self):
  self.need();self.assertEqual(self.m.embedded(fixture())['text'],'原文。')
 def test_not_audio_json(self):
  self.need();self.assertIsNone(self.m.embedded(atom(b'mdat','{"attributedString":{"runs":["假",0]}}'.encode())))
 def test_truncated_atom_rejected(self):
  self.need()
  with self.assertRaises(ValueError):self.m.embedded(fixture()[:-3])
 def test_duplicate_transcripts_rejected(self):
  self.need()
  with self.assertRaises(ValueError):self.m.embedded(fixture()+fixture('另一份'))
 def test_unknown_runs_rejected(self):
  self.need();bad={'attributedString':{'runs':['原文',{'unknown':1}]}}
  with self.assertRaises(ValueError):self.m.embedded(atom(b'moov',atom(b'udta',atom(b'tsrp',json.dumps(bad).encode()))))
 def test_tampering_and_missing_polished_block_verification(self):
  self.need()
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);(p/'a.m4a').write_bytes(b'a');(p/'raw.txt').write_text('原文');(p/'edit.txt').write_text('整理')
   manifest={'files':{n:self.m.sha(p/n) for n in ['a.m4a','raw.txt','edit.txt']}}
   self.m.check_files(p,manifest)
   (p/'a.m4a').write_bytes(b'b')
   with self.assertRaises(ValueError):self.m.check_files(p,manifest)
   (p/'a.m4a').write_bytes(b'a');(p/'edit.txt').unlink()
   with self.assertRaises(ValueError):self.m.check_files(p,manifest)
 def test_content_title_is_safe_and_not_empty(self):
  self.need();self.assertTrue(hasattr(self.m, 'safe_title'), 'Content-based filenames are not supported')
  self.assertEqual(self.m.safe_title('  会议/讨论:方案  '),'会议_讨论_方案')
  self.assertLessEqual(len(self.m.safe_title('题'*100)),60)
  with self.assertRaises(ValueError):self.m.safe_title('   ')
 def test_existing_output_never_overwritten(self):
  self.need()
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);p.joinpath('keep').write_text('safe')
   with self.assertRaises(FileExistsError):self.m.new_output(p)
   self.assertEqual(p.joinpath('keep').read_text(),'safe')
if __name__=='__main__':unittest.main()
