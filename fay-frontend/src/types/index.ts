export type LiveState = 0 | 1 | 2 | 3;

export type UserRecord = [number, string, string?] & {
  showDelete?: boolean;
};

export interface MessageRecord {
  id?: number | string;
  type: 'fay' | 'user' | string;
  content: string;
  timetext?: string;
  username?: string;
  uid?: number;
  session_id?: number;
  images?: string[];
  is_adopted?: 0 | 1;
  thinkExpanded?: boolean;
  thinkLoading?: boolean;
  prestartExpanded?: boolean;
  shareSelected?: boolean;
}

export interface MessageHistoryResponse {
  list: MessageRecord[];
  total: number;
  hasMore: boolean;
}

export interface SystemStatus {
  server: boolean;
  digital_human: boolean;
  remote_audio: boolean;
}

export interface VoiceOption {
  id?: string;
  name?: string;
  value?: string;
  label?: string;
}

export type DigitalHumanType = 'live2d' | 'iframe' | 'image';

export interface DigitalHumanPersona {
  gender?: string;
  age?: string;
  birth?: string;
  zodiac?: string;
  constellation?: string;
  position?: string;
  goal?: string;
  job?: string;
  contact?: string;
  additional?: string;
  [key: string]: any;
}

export interface DigitalHuman {
  id: string;
  name: string;
  type: DigitalHumanType;
  cover_url: string;
  render_url: string;
  voice: string;
  tags: string[];
  persona: DigitalHumanPersona;
  enabled: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface DigitalHumanPayload {
  id?: string;
  name?: string;
  type?: DigitalHumanType;
  cover_url?: string;
  render_url?: string;
  voice?: string;
  tags?: string[];
  persona?: DigitalHumanPersona;
  enabled?: boolean;
}

export interface FayConfig {
  source?: Record<string, any>;
  attribute?: Record<string, any>;
  interact?: Record<string, any>;
  memory?: Record<string, any>;
  items?: any[];
  digital_humans?: {
    active_id?: string;
    items?: DigitalHuman[];
  };
}

export interface ConfigDataResponse {
  config: FayConfig;
  voice_list?: VoiceOption[];
}

export interface ExecutionStatus {
  status: 'idle' | 'running' | 'done' | 'failed' | 'cancelled' | string;
  username?: string;
  original_request?: string;
  current_step?: string;
  steps_done?: number;
  progress_messages?: string[];
  elapsed?: number;
  error?: string | null;
}

export interface WebsocketPayload {
  liveState?: LiveState;
  voiceList?: VoiceOption[];
  deviceList?: string[];
  digitalHuman?: DigitalHuman;
  digitalHumanActiveId?: string;
  panelMsg?: string;
  panelReply?: MessageRecord;
  robot?: string;
  is_connect?: boolean;
  remote_audio_connect?: boolean;
}
