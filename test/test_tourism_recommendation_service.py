import os
import shutil
import sys
import tempfile
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.tourism_recommendation_service import TourismRecommendationService


class TourismRecommendationServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='fay-tour-rec-')
        self.db_path = os.path.join(self.temp_dir, 'tourism_recommendation.db')
        self.service = TourismRecommendationService(db_path=self.db_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_schema_is_created_with_core_tables(self):
        tables = self.service.list_tables()

        self.assertIn('recommendation_attraction', tables)
        self.assertIn('recommendation_route_template', tables)
        self.assertIn('recommendation_log', tables)
        self.assertIn('recommendation_user_preference', tables)

    def test_admin_data_can_be_saved_and_read(self):
        attraction_id = self.service.upsert_attraction({
            'name': '古城墙',
            'category': '历史遗迹',
            'tags': ['history', 'culture'],
            'visit_minutes': 35,
            'difficulty': 2,
            'indoor': False,
            'enabled': True,
        })
        template_id = self.service.upsert_route_template({
            'name': '历史文化半日线',
            'summary': '按时间顺序串联核心历史点位',
            'interest_tags': ['history'],
            'duration_minutes': 120,
            'enabled': True,
        })
        self.service.upsert_route_stop(template_id, attraction_id, order_index=1, stay_minutes=35)
        self.service.upsert_explanation_material(attraction_id, 'history', '城墙讲解', '从建城背景讲到防御体系。')

        template = self.service.get_route_template(template_id)
        attraction = self.service.get_attraction(attraction_id)
        materials = self.service.list_explanation_materials(attraction_id)

        self.assertEqual('历史文化半日线', template['name'])
        self.assertEqual(['history', 'culture'], attraction['tags'])
        self.assertEqual('从建城背景讲到防御体系。', materials[0]['script'])

    def test_recommendation_differs_by_interest(self):
        self._seed_history_and_nature_data()

        history = self.service.recommend({'user_id': 7, 'interests': ['history'], 'time_budget_minutes': 120})
        nature = self.service.recommend({'user_id': 7, 'interests': ['nature'], 'time_budget_minutes': 120})

        self.assertEqual('历史文化半日线', history['main_route']['name'])
        self.assertEqual('自然风光慢游线', nature['main_route']['name'])
        self.assertNotEqual(history['main_route']['id'], nature['main_route']['id'])
        self.assertTrue(history['main_route']['score_breakdown']['interest_match'] > 0)

    def test_disabled_stop_is_replaced_with_enabled_alternative(self):
        history_id, nature_id, closed_id = self._seed_history_and_nature_data()
        self.service.set_attraction_enabled(closed_id, False)
        self.service.upsert_route_edge(history_id, nature_id, walk_minutes=12, distance_meters=800)

        result = self.service.recommend({'user_id': 8, 'interests': ['history', 'nature'], 'time_budget_minutes': 180})
        stop_names = [item['name'] for item in result['main_route']['stops']]

        self.assertNotIn('古城墙', stop_names)
        self.assertIn('湖畔栈道', stop_names)
        self.assertTrue(result['main_route']['risks'])

    def test_user_preferences_can_be_saved_read_and_deleted(self):
        saved = self.service.save_user_preferences(9, {
            'interests': ['history'],
            'intensity': 'low',
            'avoid_items': ['stairs'],
        })

        loaded = self.service.get_user_preferences(9)
        self.service.delete_user_preferences(9)

        self.assertEqual(9, saved['user_id'])
        self.assertEqual(['history'], loaded['interests'])
        self.assertIsNone(self.service.get_user_preferences(9))

    def test_recommendation_generates_speakable_script_without_llm(self):
        self._seed_history_and_nature_data()

        result = self.service.recommend({'user_id': 10, 'interests': ['history'], 'time_budget_minutes': 120})
        first_stop = result['main_route']['stops'][0]

        self.assertIn('explanation_focus', first_stop)
        self.assertIn('script', first_stop)
        self.assertTrue(first_stop['script'])
        self.assertIn('alternatives', result)

    def _seed_history_and_nature_data(self):
        attractions = self._seed_attractions()
        templates = self._seed_templates()
        self._seed_stops(templates, attractions)
        self._seed_materials(attractions)
        return attractions['history'], attractions['nature'], attractions['history']

    def _seed_attractions(self):
        history_id = self.service.upsert_attraction({
            'name': '古城墙',
            'category': '历史遗迹',
            'tags': ['history', 'culture'],
            'visit_minutes': 35,
            'difficulty': 2,
            'indoor': False,
            'enabled': True,
            'popularity': 80,
            'satisfaction': 4.5,
        })
        museum_id = self.service.upsert_attraction({
            'name': '城史馆',
            'category': '博物馆',
            'tags': ['history', 'indoor'],
            'visit_minutes': 40,
            'difficulty': 1,
            'indoor': True,
            'enabled': True,
            'popularity': 70,
            'satisfaction': 4.7,
        })
        nature_id = self.service.upsert_attraction({
            'name': '湖畔栈道',
            'category': '自然风光',
            'tags': ['nature', 'photo'],
            'visit_minutes': 45,
            'difficulty': 1,
            'indoor': False,
            'enabled': True,
            'popularity': 90,
            'satisfaction': 4.8,
        })
        garden_id = self.service.upsert_attraction({
            'name': '花谷',
            'category': '自然风光',
            'tags': ['nature'],
            'visit_minutes': 35,
            'difficulty': 1,
            'indoor': False,
            'enabled': True,
            'popularity': 65,
            'satisfaction': 4.3,
        })
        return {'history': history_id, 'museum': museum_id, 'nature': nature_id, 'garden': garden_id}

    def _seed_templates(self):
        history_template = self.service.upsert_route_template({
            'name': '历史文化半日线',
            'summary': '历史兴趣优先',
            'interest_tags': ['history'],
            'duration_minutes': 120,
            'enabled': True,
        })
        nature_template = self.service.upsert_route_template({
            'name': '自然风光慢游线',
            'summary': '自然风光优先',
            'interest_tags': ['nature'],
            'duration_minutes': 120,
            'enabled': True,
        })
        return {'history': history_template, 'nature': nature_template}

    def _seed_stops(self, templates, attractions):
        history_template = templates['history']
        nature_template = templates['nature']
        history_id = attractions['history']
        museum_id = attractions['museum']
        nature_id = attractions['nature']
        garden_id = attractions['garden']
        self.service.upsert_route_stop(history_template, history_id, 1, 35)
        self.service.upsert_route_stop(history_template, museum_id, 2, 40)
        self.service.upsert_route_stop(nature_template, nature_id, 1, 45)
        self.service.upsert_route_stop(nature_template, garden_id, 2, 35)

    def _seed_materials(self, attractions):
        history_id = attractions['history']
        museum_id = attractions['museum']
        nature_id = attractions['nature']
        garden_id = attractions['garden']
        self.service.upsert_explanation_material(history_id, 'history', '城墙讲解', '从建城背景讲到防御体系。')
        self.service.upsert_explanation_material(museum_id, 'history', '文物讲解', '重点介绍出土文物与城市记忆。')
        self.service.upsert_explanation_material(nature_id, 'nature', '生态讲解', '介绍湿地生态与观景角度。')
        self.service.upsert_explanation_material(garden_id, 'nature', '植物讲解', '介绍花期、植物种类和拍照点。')


if __name__ == '__main__':
    unittest.main()
