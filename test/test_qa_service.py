import csv
import os
import sys
import tempfile
import unittest
from unittest.mock import patch


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.qa_service import QAService
from utils import config_util as cfg


class QAServiceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.qna_path = os.path.join(self.tmp.name, 'qa.csv')
        cfg.config = {'interact': {'QnA': self.qna_path}}

    def tearDown(self):
        self.tmp.cleanup()

    def _write_rows(self, rows):
        with open(self.qna_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Question', 'Answer', 'Action'])
            writer.writerows(rows)

    def test_selects_highest_scoring_qa_candidate_deterministically(self):
        self._write_rows([
            ['门票多少钱', '精确答案', ''],
            ['门票', '泛化答案', ''],
        ])

        with patch('random.choice', side_effect=lambda candidates: candidates[-1]):
            answer, source = QAService().question('qa', '门票多少钱')

        self.assertEqual('qa', source)
        self.assertEqual('精确答案', answer)

    def test_csv_action_column_is_disabled_by_default(self):
        self._write_rows([['打开程序', '已处理', 'calc.exe']])

        with patch('core.qa_service.MyThread') as thread_cls:
            answer, source = QAService().question('qa', '打开程序')

        self.assertEqual(('已处理', 'qa'), (answer, source))
        thread_cls.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
