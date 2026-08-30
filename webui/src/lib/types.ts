export type ServerSummary = {
  uuid: string;
  name: string;
  lastSeen: string | null;
  membersCount: number;
};

export type MemberView = {
  uuid: string;
  exp: number;
  player: {
    uuid: string;
    name: string;
    hidden: boolean;
  };
  level: {
    uuid: string;
    value: number;
    exp: number;
  } | null;
};

export type ServerDetail = {
  uuid: string;
  discordId: string;
  name: string;
  channel: string | null;
  lastSeen: string | null;
  members: MemberView[];
  top10: MemberView[];
};

export type LevelPoint = {
  uuid: string;
  value: number;
  exp: number;
  membersCount: number;
};
