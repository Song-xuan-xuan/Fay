import os
from dataclasses import dataclass

from core.dashboard_explanation import build_dashboard_explanation
from core.dashboard_operational import (
    classify_question_topic,
    hot_topics,
    mask_email,
    operational_summary,
    service_trends,
    user_metrics,
)
from core.dashboard_tourism import import_tourism_excel, normalize_excel_text
from core.dashboard_tourism_metrics import get_tourism_metrics, get_tourism_summary


DASHBOARD_ATTRACTIONS = ('灵山胜境', '禅意小镇·拈花湾')
DEFAULT_DASHBOARD_ATTRACTION = DASHBOARD_ATTRACTIONS[0]


@dataclass(frozen=True)
class DashboardPaths:
    project_root: str = os.getcwd()
    fay_db_path: str = os.path.join('memory', 'fay.db')
    user_db_path: str = os.path.join('memory', 'user_profiles.db')
    tourism_db_path: str = os.path.join('memory', 'tourism.db')
    tourism_excel_path: str = os.path.join('data', '景点景区旅游数据行为分析数据.xlsx')


def repair_text(value):
    return normalize_excel_text(value)


class DashboardService:
    def __init__(self, paths=None):
        self.paths = paths or self.default_paths()

    @classmethod
    def default_paths(cls):
        root = os.getcwd()
        return DashboardPaths(
            project_root=root,
            fay_db_path=os.path.join(root, 'memory', 'fay.db'),
            user_db_path=os.path.join(root, 'memory', 'user_profiles.db'),
            tourism_db_path=os.path.join(root, 'memory', 'tourism.db'),
            tourism_excel_path=_find_tourism_excel(root),
        )

    def import_tourism_excel(self, force=False):
        return import_tourism_excel(self.paths.tourism_db_path, self.paths.tourism_excel_path, force=force)

    def get_overview(self, range_key='7d', is_admin=False, tourism_filters=None):
        self.import_tourism_excel(force=False)
        operations = operational_summary(self.paths.fay_db_path, range_key)
        users = user_metrics(self.paths.user_db_path, is_admin=is_admin)
        tourism = get_tourism_summary(self.paths.tourism_db_path, tourism_filters or {})
        kpis = [
            _kpi('今日服务人次', operations['today_services'], '人次', '全局运营数据'),
            _kpi('本周服务人次', operations['week_services'], '人次', '全局运营数据'),
            _kpi('今日问答次数', operations['today_questions'], '次', '全局运营数据'),
            _kpi('今日新增注册', users['today_new_users'], '人', '全局用户数据'),
            _kpi('累计注册用户', users['total_users'], '人', '全局用户数据'),
            _kpi('本周活跃用户', users['week_active_users'], '人', '全局用户数据'),
            _kpi('游客平均满意度', tourism.get('average_satisfaction', 0), '分', '当前景区数据'),
            _kpi('低满意预警', tourism.get('low_satisfaction_count', 0), '条', '当前景区数据'),
        ]
        return {
            'is_demo': False,
            'data_source': 'system_sqlite_and_excel',
            'kpis': kpis,
            'operations': operations,
            'users': users,
            'tourism_source': tourism.get('source', {}),
        }

    def get_service_trends(self, range_key='7d'):
        return {'range': range_key, 'items': service_trends(self.paths.fay_db_path, range_key)}

    def get_hot_topics(self, range_key='7d'):
        return {'range': range_key, 'items': hot_topics(self.paths.fay_db_path, range_key)}

    def get_user_metrics(self, is_admin=False):
        return user_metrics(self.paths.user_db_path, is_admin=is_admin)

    def get_tourism(self, filters):
        self.import_tourism_excel(force=False)
        return get_tourism_metrics(self.paths.tourism_db_path, filters or {})

    def explain(self, payload):
        return build_dashboard_explanation(payload, self)


def _find_tourism_excel(root):
    candidates = [
        os.path.join(root, 'data', 'imports', 'tourism_behavior.xlsx'),
        os.path.join(root, 'data', '景点景区旅游数据行为分析数据.xlsx'),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[-1]


def _kpi(title, value, unit, source):
    return {'title': title, 'value': value, 'unit': unit, 'source': source, 'is_demo': False, 'change': 0}
