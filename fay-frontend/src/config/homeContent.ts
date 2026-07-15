export interface HomeRoute {
  name: string;
  duration: string;
  note: string;
  stops: string[];
}

export const HOME_SECTIONS = [
  { id: 'hero', label: '境语 AI' },
  { id: 'guide', label: '数字人导览' },
  { id: 'rag', label: '知识检索' },
  { id: 'route', label: '路线推荐' },
  { id: 'network', label: '能力网络' },
  { id: 'insights', label: '数据洞察' },
  { id: 'cta', label: '进入系统' },
] as const;

export const HOME_RAG_QUESTIONS = [
  {
    question: '灵山大佛为什么建在这里？',
    answer: '灵山胜境依托马山山水格局与祥符禅寺历史文脉建设。灵山大佛通高 88 米，面向太湖，是景区的核心文化景观。',
    references: ['景区历史沿革', '灵山大佛结构化条目', '祥符禅寺文化资料'],
  },
  {
    question: '梵宫最值得关注的是什么？',
    answer: '灵山梵宫汇集木雕、琉璃、壁画等艺术，也是世界佛教论坛相关活动的重要场所。',
    references: ['灵山梵宫结构化条目', '景区文化特色', '核心景点资料'],
  },
  {
    question: '带孩子游览适合哪些点位？',
    answer: '亲子游可重点体验九龙灌浴、佛手广场、百子戏弥勒、灵山梵宫与五印坛城，兼顾演出、互动与文化体验。',
    references: ['亲子家庭 4 小时路线', '九龙灌浴条目', '百子戏弥勒条目'],
  },
] as const;

export const HOME_ROUTES: HomeRoute[] = [
  {
    name: '历史文化深度游',
    duration: '6 小时',
    note: '循中轴而上，读懂造像、建筑与佛教文化。',
    stops: ['南门入园', '灵山大照壁（华夏第一壁）', '胜境广场', '佛手广场（天下第一掌）', '祥符禅寺', '杏坛广场', '佛前广场', '灵山大佛', '灵山梵宫', '五印坛城', '三圣殿', '出口'],
  },
  {
    name: '自然风光全景游',
    duration: '',
    note: '一路串联太湖视野、园林景致与文化地标。',
    stops: ['南门入园', '佛足坛', '九龙灌浴', '菩提大道', '灵山大佛', '曼飞龙塔', '灵山精舍', '梵宫广场', '出口'],
  },
  {
    name: '亲子家庭轻松游',
    duration: '',
    note: '轻松看演出、赏雕塑，体验适合全家的灵山。',
    stops: ['南门入园', '九龙灌浴', '佛手广场', '百子戏弥勒', '灵山梵宫', '五印坛城', '出口'],
  },
];

export const HOME_CAPABILITIES = [
  { key: 'ASR', label: '实时语音识别', detail: '自然交流，即时响应' },
  { key: 'RAG', label: '景区知识检索', detail: '答案有据，讲解可信' },
  { key: 'ROUTE', label: '智能路线推荐', detail: '按时间与偏好生成游线' },
  { key: 'MCP', label: '服务能力连接', detail: '连接景区工具与服务' },
  { key: 'DATA', label: '游客数据洞察', detail: '从游览记录发现需求' },
] as const;

export const HOME_INSIGHTS = [
  { label: '平均游览时长', value: '3.99', unit: '小时' },
  { label: '平均同行人数', value: '2.71', unit: '人' },
  { label: '平均满意度', value: '3.04', unit: '/ 5' },
  { label: '匿名游览记录', value: '236', unit: '条' },
] as const;

export const HOME_ASSETS = {
  backgroundUrl: import.meta.env.VITE_HOME_BACKGROUND_URL || '',
  ambientAudioUrl: import.meta.env.VITE_HOME_AMBIENT_AUDIO_URL || '',
  defaultHumanCover: 'https://cdn.jsdelivr.net/gh/Song-xuan-xuan/PicGo_image@main/img/image-20260612161741081.png',
  localHumanCover: '/frontend-static/images/digital-human-default.gif',
};
